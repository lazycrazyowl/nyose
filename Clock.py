from time import sleep

class Clock(object):
	def __init__(self, interval = 5.0, notiSoon = 10, dayend = 2340):
		self.interval = interval
		self.notiSoon = notiSoon
		self.dayend = dayend
		self.sent = False
		self.exit = False

	def config(self, new_conf):
		if new_conf[0] > 0:
			print "change interval"
			self.interval = int(new_conf[0])
		if new_conf[1] > 0:
			print "change noti interval"
			self.notiSoon = int(new_conf[1])
		if new_conf[2] > 0:
			print "change dayend point"
			self.dayend = int(new_conf[2])
		if new_conf[3]:
			print "received terminal signal"
			self.exit = True

	def checkAndDo(self, time, tenw, wtab, jnal, plan, mail):

		# Priority 01: Reminder
		time.update()
		comingStamp = plan.thereIsComingEvent(time, self.notiSoon)
		if not (comingStamp is False) and comingStamp < self.dayend:
			print 'send notification at {} of {}'.format(
				time.timeStamp, time.tdSig)
			mail.send(plan.eventMailFormat(comingStamp))
			plan.noti.add(comingStamp)

		# Priority 02: Order from the master
		mail.update()
		if mail.received(): # Set latest processed received email Sigature here
			print 'received order at {} of {}'.format(
				time.timeStamp, time.tdSig)
			time.update()

			self.config(mail.conf())
			if mail.howto():
				mail.doHowto()
			if mail.plan():
				mail.doPlan(plan) # Send comfirmation inside
			if mail.jnal():
				mail.doJournal(plan, jnal, time) # Send confirmation inside
			if mail.wtab():
				mail.doWeekTable(wtab) # Send confirmation inside
			if mail.tenw():
				mail.doTenWeek(time, plan, tenw, self.dayend) # Send confirmation inside
			mail.allProcessed()
			print "all processed"

		# Priority 03: Day end, next day planning + revive
		time.update()
		dayendNoPlan = time.timeStamp >= self.dayend and time.tdSig >= plan.newestPlanSig
		daybeingNoPlan = time.timeStamp < self.dayend and time.tdSig > plan.newestPlanSig
		# If both is false, planFor is for today
		planFor = dayendNoPlan * time.tmrSig + (not dayendNoPlan) * time.tdSig
		if dayendNoPlan or daybeingNoPlan:
			print "log down journal {}".format(time.tdSig)
			jnal.logdown(time) # anything happen next belong to next day.
			print "dump plan {}".format(plan.newestPlanSig)
			plan.dump()
			print "clean communications"
			mail.clean()
			plan.sketch(time, wtab, tenw, self.dayend) # this set the newestPlan to a new one.
			self.sent = False
		
		# Priority 04: System just start
		if not self.sent:

			print "send notice list {}".format(planFor)
			tenw.revive(planFor) # because tenw.todayNotice is not for dump and load at __init__
			mail.send(tenw.todayDlMailFormat(time, self.dayend))
			
			print "send plan {}".format(planFor)
			mail.send(plan.mailFormat())
			self.sent = True

	def run(self, time, tenw, wtab, jnal, plan, mail):
		print "running loop"
		try:
			# Infinite loop until master send EXIT email.
			while not self.exit:
				self.checkAndDo(time, tenw, wtab, jnal, plan, mail)
				sleep(self.interval)
		except:
				print '\nsomething wrong, skipped to next loop'
				sleep(self.interval)
		finally:
			print "\ndump plan and journal before exiting"
			plan.dump()
			jnal.logdown(time)

			print "clean and say goodbye"
			mail.clean()
			mail.sendExit()