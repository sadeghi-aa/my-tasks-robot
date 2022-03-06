from local_settings import *

try:
    import sys
    from flask import Flask, request
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    from datetime import datetime
    from math import ceil, floor
    import dateparser
    from dateparser.calendars.jalali import JalaliCalendar
    from pytz import timezone
    from traceback import format_exc
    from geopy import geocoders
    from timezonefinder import TimezoneFinder
    # from database import db, SQLALCHEMY_DATABASE_URI, User, Task
    from persiantools.jdatetime import JalaliDate
    # from flask_sqlalchemy import and_
    from flask_sqlalchemy import SQLAlchemy
    import re
except:
    import telebot, traceback, sys
    bot = telebot.TeleBot(token, threaded=False)
    bot.send_message(me, traceback.format_exc())
    sys.exit()

try:
    wait_tz = 'WAIT_TZ'
    idle = 'IDLE'
    wait_date = 'WAIT_DATE'
    wait_name = 'WAIT_NAME'
    wait_type = 'WAIT_TYPE'
    wait_cal = 'WAIT_CAL'
    toggle = ['enable', 'disable']
    timestamp_change = {'daily': 86400, 'weekly': 604800}
    tehran, istanbul, paris, london, newyork, chicago, edmonton, vancouver = "Asia/Tehran", "Europe/Istanbul", "Europe/Paris", "Europe/London", "America/New_York", "America/Chicago", "America/Edmonton", "America/Vancouver"
    hourglass, brhombus, man_running, calendar, clock, speaker, world, passed, bell, spiral, repeat = '⏳',  '🔹', '🏃‍♂️', '📅', '⏰', '📢', '🌎', '🔻', '🔔', '🌀', '🔄'
    iran, turkey, france, uk, us, canada = '🇮🇷', '🇹🇷', '🇫🇷', '🇬🇧', '🇺🇸', '🇨🇦'
    settings_icon = '❌', '✅'

    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{db_username}:{db_password}@{hostname}/{db_name}"
    # db = SQLAlchemy()

    app = Flask(__name__)
    app.config["DEBUG"] = True

    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db = SQLAlchemy(app)
    bot = telebot.TeleBot(token, threaded=False)
    class Task(db.Model):
        __tablename__ = "tasks"

        task_id = db.Column(db.Integer, primary_key=True)
        chat_id = db.Column(db.Integer, db.ForeignKey('users.chat_id'), nullable=False)
        name = db.Column(db.String(100), nullable=False)
        timestamp = db.Column(db.Integer)
        notified_two_hours = db.Column(db.Boolean, default=False, nullable=False)
        notified_one_day = db.Column(db.Boolean, default=False, nullable=False)
        type = db.Column(db.String, default='one-time', nullable=False)


    class User(db.Model):
        __tablename__ = "users"

        chat_id = db.Column(db.Integer, primary_key=True)
        status = db.Column(db.String(100), nullable=False, default=wait_name)
        total = db.Column(db.Boolean, default=True, nullable=False)
        dif = db.Column(db.Boolean, default=False, nullable=False)
        due = db.Column(db.Boolean, default=False, nullable=False)
        calendar = db.Column(db.String(10))
        timezone = db.Column(db.String(100), default=None)
        date_joined = db.Column(db.DateTime, nullable=False)
        notify_two_hours = db.Column(db.Boolean, default=False, nullable=False)
        notify_one_day = db.Column(db.Boolean, default=False, nullable=False)


    def log_error(s):
        try:
            bot.send_message(me, s)
        except:
            with open('errors.txt', 'a') as f:
                f.write(f'{s}\n\n')
except:
    bot = telebot.TeleBot(token, threaded=False)
    bot.send_message(me, format_exc())
    sys.exit()


# db.init_app(app)

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    except:
        error = format_exc()
        sorry = '\n'.join(
            ["Sorry. Looks like you've found a bug. It's OK. I've got the error details and will try to fix it as soon as possible.",
            '',
            f"Meanwhile, it would help a lot if you describe the last thing you were trying to do before you saw this error and send it to {tg_username}",
            '',
            "Thank you!"])
        if update.message:
            bot.send_message(update.message.chat.id, sorry)
            error_report = '\n'.join(
                [f"User: {update.message.chat.id}",
                '',
                error])
        elif update.callback_query:
            bot.send_message(update.callback_query.from_user.id, sorry)
            error_report = '\n'.join(
                [f"User: {update.callback_query.from_user.id}",
                '',
                error])

        log_error(error_report)
        return "Bad request", 400
    return "!", 200


@app.route('/notify' + token, methods=['GET'])
def notify():
    try:
        text = '\n'.join(
            [f'{repeat} Recurring Tasks',
            '',
            'From now on you can have daily and weekly tasks, as well as one-time tasks.',
            '',
            'Deadlines for recurring tasks get updated every day or week depending on the task type.'])
        users = User.query.all()
        for user in users:
            try:
                if True:
                    bot.send_message(user.chat_id, text, parse_mode='HTML', disable_web_page_preview=True)
            except:
                pass
        return "!", 200
    except:
        log_error(format_exc())
        return "!", 400


# @celery.task
def run_cron_job():
    now_time = datetime.now().timestamp()
    two_hr_later = now_time + 7200
    one_day_later = now_time + 86400
    two_hr_users = User.query.filter(User.notify_two_hours == 1).all()
    # bot.send_message(me, two_hr_users)
    recurring_tasks = Task.query.filter(Task.type != 'one-time').all()
    task_changed = False
    for task in recurring_tasks:
        if task.timestamp < datetime.now().timestamp():
            task_changed = True
            task.timestamp += timestamp_change[task.type]
    if task_changed:
        db.session.commit()

    for user in two_hr_users:
        two_hr_tasks = Task.query.join(User)\
            .filter(Task.chat_id == user.chat_id)\
            .filter((Task.timestamp <= two_hr_later) & (Task.timestamp >= now_time) & (Task.notified_two_hours == 0))\
            .order_by(Task.timestamp)\
            .all()
        two_hr_tasks.sort(key=lambda o: o.timestamp)

        # bot.send_message(me, len(two_hr_tasks))
        full_text = ["<b>Upcoming deadlines in 2 hours:</b>"]
        for task in two_hr_tasks:
            task_name = task.name
            deadline = datetime.fromtimestamp(task.timestamp)
            now = datetime.now()
            rem_time = deadline - now
            days = rem_time.days
            seconds = rem_time.seconds
            total_rem_time = []
            happening = False
            if days < 0:
                seconds = seconds - 86400
                days = days + 1
                hours = ceil(seconds / 3600)
                minutes = ceil((seconds - hours * 3600) / 60)
                happening = (days + hours == 0) and seconds > -60
            else:
                hours = floor(seconds / 3600)
                minutes = floor((seconds - hours * 3600) / 60)

            task_emoji = brhombus
            if days <= 0:
                if happening:
                    task_emoji = bell
                elif days + hours + minutes < 0:
                    task_emoji = passed
                else:
                    task_emoji = man_running

            name = f"{task_emoji} <b>{task_name}</b>"
            text = [name]


            if happening:
                total_rem_time = 'Now'
            elif minutes + hours + days == 0:
                total_rem_time = 'Less than a minute'
            else:
                if days:
                    unit = ' Days'
                    if abs(days) == 1:
                        unit = ' Day'
                    total_rem_time.append(str(days) + unit)
                if hours:
                    unit = ' Hours'
                    if abs(hours) == 1:
                        unit = ' Hour'
                    total_rem_time.append(str(hours) + unit)
                unit = ' Minutes'
                if minutes:
                    if abs(minutes) == 1:
                        unit = ' Minute'
                    total_rem_time.append(str(minutes) + unit)
                total_rem_time = ', '.join(total_rem_time)


            if not happening:
                total_rem_time = ' '.join([hourglass, total_rem_time])
            else:
                total_rem_time = ' '.join([spiral, total_rem_time])
            text.append(total_rem_time)
            delete_command = f"/delete_{task.task_id}"
            calendar_type = user.calendar
            local_timezone = timezone(user.timezone)
            local_due = deadline.astimezone(local_timezone)
            local_duetime = "{0:%H}:{0:%M}".format(local_due)
            if calendar_type == "Gregorian":
                if local_due.year == now.astimezone(local_timezone).year:
                    local_duedate = "{0:%a}, {0:%b} {0.day}".format(local_due)
                else:
                    local_duedate = "{0:%a}, {0:%b} {0.day}, {0.year}".format(local_due)
            else:
                local_due = JalaliDate(local_due)
                if local_due.year == JalaliDate(now.astimezone(local_timezone)).year:
                    local_duedate = "{0:%a}, {0:%B} {0.day}".format(local_due)
                else:
                    local_duedate = "{0:%a}, {0:%B} {0.day}, {0.year}".format(local_due)
            text.append(f"{calendar} {local_duedate} {clock} {local_duetime}")
            if task.type != 'one-time':
                text.append(f'{repeat} {task.type[0].upper() + task.type[1:]} Task')
            text.append(delete_command)
            text = '\n'.join(text)
            full_text.append(text)
        full_text = '\n\n'.join(full_text)
        if len(two_hr_tasks) > 0:
            bot.send_message(user.chat_id, full_text, parse_mode='HTML')
        for task in two_hr_tasks:
            task.notified_two_hours = 1
            db.session.commit()


    one_day_users = User.query.filter(User.notify_one_day == 1).all()
    for user in one_day_users:
        one_day_tasks = Task.query.join(User)\
            .filter(Task.chat_id == user.chat_id)\
            .filter((Task.timestamp <= one_day_later) & (Task.timestamp >= now_time) & (Task.notified_one_day == 0))\
            .order_by(Task.timestamp).all()
        one_day_tasks.sort(key=lambda o: o.timestamp)
        # bot.send_message(me, len(one_day_tasks))
        full_text = ["<b>Upcoming deadlines in 24 hours:</b>"]
        for task in one_day_tasks:
            task_name = task.name
            deadline = datetime.fromtimestamp(task.timestamp)
            now = datetime.now()
            rem_time = deadline - now
            days = rem_time.days
            seconds = rem_time.seconds
            total_rem_time = []
            happening = False
            if days < 0:
                seconds = seconds - 86400
                days = days + 1
                hours = ceil(seconds / 3600)
                minutes = ceil((seconds - hours * 3600) / 60)
                happening = (days + hours == 0) and seconds > -60
            else:
                hours = floor(seconds / 3600)
                minutes = floor((seconds - hours * 3600) / 60)

            task_emoji = brhombus
            if days <= 0:
                if happening:
                    task_emoji = bell
                elif days + hours + minutes < 0:
                    task_emoji = passed
                else:
                    task_emoji = man_running

            name = f"{task_emoji} <b>{task_name}</b>"
            text = [name]


            if happening:
                total_rem_time = 'Now'
            elif minutes + hours + days == 0:
                total_rem_time = 'Less than a minute'
            else:
                if days:
                    unit = ' Days'
                    if abs(days) == 1:
                        unit = ' Day'
                    total_rem_time.append(str(days) + unit)
                if hours:
                    unit = ' Hours'
                    if abs(hours) == 1:
                        unit = ' Hour'
                    total_rem_time.append(str(hours) + unit)
                unit = ' Minutes'
                if minutes:
                    if abs(minutes) == 1:
                        unit = ' Minute'
                    total_rem_time.append(str(minutes) + unit)
                total_rem_time = ', '.join(total_rem_time)


            if not happening:
                total_rem_time = ' '.join([hourglass, total_rem_time])
            else:
                total_rem_time = ' '.join([spiral, total_rem_time])
            text.append(total_rem_time)
            delete_command = f"/delete_{task.task_id}"
            calendar_type = user.calendar
            local_timezone = timezone(user.timezone)
            local_due = deadline.astimezone(local_timezone)
            local_duetime = "{0:%H}:{0:%M}".format(local_due)
            if calendar_type == "Gregorian":
                if local_due.year == now.astimezone(local_timezone).year:
                    local_duedate = "{0:%a}, {0:%b} {0.day}".format(local_due)
                else:
                    local_duedate = "{0:%a}, {0:%b} {0.day}, {0.year}".format(local_due)
            else:
                local_due = JalaliDate(local_due)
                if local_due.year == JalaliDate(now.astimezone(local_timezone)).year:
                    local_duedate = "{0:%a}, {0:%B} {0.day}".format(local_due)
                else:
                    local_duedate = "{0:%a}, {0:%B} {0.day}, {0.year}".format(local_due)
            text.append(f"{calendar} {local_duedate} {clock} {local_duetime}")
            text.append(delete_command)
            text = '\n'.join(text)
            full_text.append(text)
        full_text = '\n\n'.join(full_text)
        if len(one_day_tasks) > 0:
            bot.send_message(user.chat_id, full_text, parse_mode='HTML')
        for task in one_day_tasks:
            task.notified_one_day = 1
            db.session.commit()
    return


@app.route('/cron' + token, methods=['GET'])
def cron():
    try:
        run_cron_job()
        return "!", 200
    except:
        log_error(traceback.format_exc())
        return "!", 400


def cleanup(message):
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if user:
        if user.status != idle:
            user.status = idle
            tasks = Task.query.filter_by(chat_id=message.chat.id, timestamp=None).all()
            for task in tasks:
                db.session.delete(task)
            db.session.commit()
            return True
        else:
            return False


def settings_text(total, due, dif, calendar_type, notify_two_hours, notify_one_day):
    text = []
    text.append('')
    text.append(f"{settings_icon[total]} Total remaining time")
    text.append(f"{settings_icon[due]} Due time")
    # text.append(f"{settings_icon[dif]} Coming soon...")
    text.append(f"{calendar} Calendar: <b>{calendar_type}</b>")
    text.append(f"{settings_icon[notify_two_hours]} Notify 2 hours before all deadlines")
    text.append(f"{settings_icon[notify_one_day]} Notify 24 hours before all deadlines")
    return '\n'.join(text)


@bot.callback_query_handler(func=lambda call: True)
def tz_select(call):
    user = User.query.filter_by(chat_id=call.from_user.id).first()
    if user and user.status == idle and call.data == 'total':
        user.total = not user.total
        total = user.total
        due = user.due
        dif = user.dif
        notify_two_hours = user.notify_two_hours
        notify_one_day = user.notify_one_day
        calendar = user.calendar
        db.session.commit()
        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)
        bot.edit_message_text(
            text,
            call.from_user.id,
            call.message.id,
            reply_markup=call.message.reply_markup,
            parse_mode='HTML')
        bot.answer_callback_query(call.id, 'Saved!')
    elif user and user.status == idle and call.data == 'due':
        user.due = not user.due
        total = user.total
        due = user.due
        dif = user.dif
        notify_two_hours = user.notify_two_hours
        notify_one_day = user.notify_one_day
        calendar = user.calendar
        db.session.commit()
        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)
        bot.edit_message_text(
            text,
            call.from_user.id,
            call.message.id,
            reply_markup=call.message.reply_markup,
            parse_mode='HTML')
        bot.answer_callback_query(call.id, 'Saved!')
    elif user and user.status == idle and call.data == 'dif':
        bot.answer_callback_query(call.id, 'Coming soon...')
    elif user and user.status == idle and call.data == 'calendar':
        total = user.total
        due = user.due
        dif = user.dif
        if user.calendar == 'Gregorian':
            user.calendar = 'Jalali'
        else:
            user.calendar = 'Gregorian'
        calendar = user.calendar
        notify_two_hours = user.notify_two_hours
        notify_one_day = user.notify_one_day
        db.session.commit()
        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)
        bot.edit_message_text(
            text,
            call.from_user.id,
            call.message.id,
            reply_markup=call.message.reply_markup,
            parse_mode='HTML')
        bot.answer_callback_query(call.id, 'Saved!')
    elif user and user.status == idle and call.data == 'notif-day':
        user.notify_one_day = not user.notify_one_day
        total = user.total
        due = user.due
        dif = user.dif
        calendar = user.calendar
        notify_two_hours = user.notify_two_hours
        notify_one_day = user.notify_one_day
        db.session.commit()
        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)
        bot.edit_message_text(
            text,
            call.from_user.id,
            call.message.id,
            reply_markup=call.message.reply_markup,
            parse_mode='HTML')
        bot.answer_callback_query(call.id, 'Saved!')
    elif user and user.status == idle and call.data == 'notif-hour':
        user.notify_two_hours = not user.notify_two_hours
        total = user.total
        due = user.due
        dif = user.dif
        calendar = user.calendar
        notify_two_hours = user.notify_two_hours
        notify_one_day = user.notify_one_day
        db.session.commit()
        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)
        bot.edit_message_text(
            text,
            call.from_user.id,
            call.message.id,
            reply_markup=call.message.reply_markup,
            parse_mode='HTML')
        bot.answer_callback_query(call.id, 'Saved!')
    elif user and user.status == wait_cal:
        if call.data in ['Gregorian', 'Jalali']:
            user.calendar = call.data
            bot.answer_callback_query(call.id, f'Calendar is set to {call.data}.')
            bot.edit_message_text(
                '\n'.join([
                    f'Calendar is now set to <b>{call.data}</b>. You can always change it in /settings. Do you want to add a /new task?']),
                call.from_user.id,
                call.message.id,
                parse_mode='HTML')
            if not user.timezone:
                bot.send_message(
                    call.from_user.id,
                    "Now let's set your /timezone."
                )
            db.session.commit()
        else:
            bot.answer_callback_query(call.id, f'Wrong button?')
    elif user and user.status == wait_tz:
        now = datetime.now()
        local_timezone = call.data
        try:
            local_now = now.astimezone(timezone(local_timezone))
            bot.edit_message_text(
                '\n'.join(
                    [f'Great! Your time zone is now set to <b>{local_timezone}</b>.',
                    f'{clock} ' + 'Current time: <b>{0:%H}:{0:%M}</b>'.format(local_now),
                    '',
                    'If this is not your local time, tap on /timezone and try sending your city name.']),
                call.from_user.id,
                call.message.id,
                parse_mode='HTML')
            user.timezone = call.data
            user.status = idle
            db.session.commit()
            bot.answer_callback_query(call.id, 'Time zone is now set.')
        except:
            bot.answer_callback_query(call.id, 'Wrong button?')
    elif user and user.status == wait_type:
        if call.data in ['one-time', 'daily', 'weekly']:
            task = Task(chat_id=call.from_user.id, type=call.data, name='')
            user.status = wait_name
            db.session.add(task)
            db.session.commit()
            bot.answer_callback_query(call.id, f'Task type was set as {call.data}.')
            bot.edit_message_text(
                f'Now enter the name of your {call.data} task:',
                call.from_user.id,
                call.message.id)
        else:
            bot.answer_callback_query(call.id, f'Wrong button?')
    else:
        bot.answer_callback_query(call.id, f'Wrong button?')


@bot.message_handler(commands=['new'])
def new(message):
    user = User.query.filter_by(chat_id=message.chat.id).first()
    cleanup(message)
    if user and user.timezone and user.calendar:
        user.status = wait_type
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(InlineKeyboardButton('One-time Task', callback_data='one-time'))
        markup.add(InlineKeyboardButton('Daily Task', callback_data='daily'),
                   InlineKeyboardButton('Weekly Task', callback_data='weekly'))
        bot.reply_to(message, '\n'.join(['Select the type of the task:']), reply_markup=markup)
    elif user and not user.timezone:
        bot.reply_to(message, '\n'.join(
            ['You need to set your time zone before adding your first task.',
            '',
            'Tap on /timezone to proceed.']))
    elif user and not user.calendar:
        bot.reply_to(message, '\n'.join(
            ['You need to set your calendar type before adding your first task.',
            '',
            'Tap on /calendar to proceed.']))

    db.session.commit()


@bot.message_handler(commands=['see'])
def see(message):
    cleanup(message)

    full_text = []
    # one_time_tasks = Task.query.filter_by(chat_id=message.chat.id, type='one-time').all()
    tasks = Task.query.filter_by(chat_id=message.chat.id).all()

    task_changed = False
    for task in tasks:
        if task.type != 'one-time' and task.timestamp < datetime.now().timestamp():
            task_changed = True
            task.timestamp += timestamp_change[task.type]
    if task_changed:
        db.session.commit()

    # tasks = [task for task in one_time_tasks] + [task for task in recurring_tasks]
    tasks.sort(key=lambda o: o.timestamp)

    if tasks:
        chat_id = message.chat.id
        user = User.query.filter_by(chat_id=message.chat.id).first()
        total = user.total
        due = user.due

        for task in tasks:
            task_name = task.name
            deadline = datetime.fromtimestamp(task.timestamp)
            now = datetime.now()
            rem_time = deadline - now
            days = rem_time.days
            seconds = rem_time.seconds
            total_rem_time = []
            happening = False
            if days < 0:
                seconds = seconds - 86400
                days = days + 1
                hours = ceil(seconds / 3600)
                minutes = ceil((seconds - hours * 3600) / 60)
                happening = (days + hours == 0) and seconds > -60
            else:
                hours = floor(seconds / 3600)
                minutes = floor((seconds - hours * 3600) / 60)

            task_emoji = brhombus
            if days <= 0:
                if happening:
                    task_emoji = bell
                elif days + hours + minutes < 0:
                    task_emoji = passed
                else:
                    task_emoji = man_running

            name = f"{task_emoji} <b>{task_name}</b>"
            text = [name]

            if total:
                if happening:
                    total_rem_time = 'Now'
                elif minutes + hours + days == 0:
                    total_rem_time = 'Less than a minute'
                else:
                    if days:
                        unit = ' Days'
                        if abs(days) == 1:
                            unit = ' Day'
                        total_rem_time.append(str(days) + unit)
                    if hours:
                        unit = ' Hours'
                        if abs(hours) == 1:
                            unit = ' Hour'
                        total_rem_time.append(str(hours) + unit)
                    unit = ' Minutes'
                    if minutes:
                        if abs(minutes) == 1:
                            unit = ' Minute'
                        total_rem_time.append(str(minutes) + unit)
                    total_rem_time = ', '.join(total_rem_time)


                if not happening:
                    total_rem_time = ' '.join([hourglass, total_rem_time])
                else:
                    total_rem_time = ' '.join([spiral, total_rem_time])
                text.append(total_rem_time)
            delete_command = f"/delete_{task.task_id}"
            if due:
                calendar_type = user.calendar
                local_timezone = timezone(user.timezone)
                local_due = deadline.astimezone(local_timezone)
                local_duetime = "{0:%H}:{0:%M}".format(local_due)
                if calendar_type == "Gregorian":
                    if local_due.year == now.astimezone(local_timezone).year:
                        local_duedate = "{0:%a}, {0:%b} {0.day}".format(local_due)
                    else:
                        local_duedate = "{0:%a}, {0:%b} {0.day}, {0.year}".format(local_due)
                else:
                    local_due = JalaliDate(local_due)
                    if local_due.year == JalaliDate(now.astimezone(local_timezone)).year:
                        local_duedate = "{0:%a}, {0:%B} {0.day}".format(local_due)
                    else:
                        local_duedate = "{0:%a}, {0:%B} {0.day}, {0.year}".format(local_due)
                text.append(f"{calendar} {local_duedate} {clock} {local_duetime}")
            if task.type != 'one-time':
                text.append(f'{repeat} {task.type[0].upper() + task.type[1:]} Task')
            text.append(delete_command)
            text = '\n'.join(text)
            full_text.append(text)
        full_text = '\n\n'.join(full_text)
        bot.send_message(chat_id, full_text, parse_mode='HTML')
    else:  # no tasks
        text = '\n'.join([
            "You don't have any tasks.",
            "Do you want to add a /new task?"])
        bot.reply_to(message, text, parse_mode='HTML')


@bot.message_handler(commands=['cancel'])
def cancel(message):
    cleaned = cleanup(message)
    if cleaned:
        bot.reply_to(message, '\n'.join(
            ['Last operation was cancelled.']))
    else:
        bot.reply_to(message, '\n'.join(
            ['OK, but nothing to cancel!']))


@bot.message_handler(commands=['settings'])
def settings(message):
    cleanup(message)
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if user:
        total = user.total
        dif = user.dif
        due = user.due
        calendar = user.calendar
        notify_one_day = user.notify_one_day
        notify_two_hours = user.notify_two_hours

        text = settings_text(total, due, dif, calendar, notify_two_hours, notify_one_day)

        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            InlineKeyboardButton('Toggle total remaining time', callback_data='total'))
        markup.add(
            InlineKeyboardButton('Toggle due time', callback_data='due'))
        # markup.add(
        #     InlineKeyboardButton('Coming soon...', callback_data='dif'))
        markup.add(
            InlineKeyboardButton('Toggle calendar', callback_data='calendar'))
        markup.add(
            InlineKeyboardButton('Toggle notification (2 hours)', callback_data='notif-hour'))
        markup.add(
            InlineKeyboardButton('Toggle notification (24 hours)', callback_data='notif-day'))

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, '\n'.join(
        ['Hello, ' + message.from_user.first_name,
        '',
        'With this bot, you can add tasks with deadlines and see how much time you have for each of them.',
        '',
        '/tutorial1']))


@bot.message_handler(commands=['tutorial1'])
def tutorial1(message):
    bot.send_message(message.chat.id, '\n'.join(
        ['Now some quick tips. Basically, you need to enter two things for each task:',
        '',
        '1- The name of the task (Perferably in English for now...)',
        '2- The deadline',
        '',
        '/tutorial2']))


@bot.message_handler(commands=['tutorial2'])
def tutorial2(message):
    bot.send_message(message.chat.id, '\n'.join(
        ["Gregorian and Persian calendars are both supported.",
        '',
        'Most common formats should work, but here are some examples (case-insensitive):',
        '',
        '۲۳ خرداد',
        '۲۳ خرداد ۲۳:۴۵',
        'May 17',
        'May 17 14:23',
        '',
        '/tutorial3']))


@bot.message_handler(commands=['tutorial3'])
def tutorial3(message):
    bot.send_message(message.chat.id, '\n'.join(
        ["After adding some tasks, you can send /see to see the remaining time until each of your tasks.",
        '',
        'The tasks will be ordered by their deadline.',
        '',
        "Before we continue, we just need to set two things: your calendar type and timezone.",
        '',
        '/calendar']))


@bot.message_handler(commands=['calendar'])
def cal(message):
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if not user:
        user = User(chat_id=message.chat.id, status=wait_cal, date_joined=datetime.now())
        db.session.add(user)
    elif user and not user.calendar:
        user.status = wait_cal
    if not user.calendar:
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton('Gregorian', callback_data='Gregorian'),
            InlineKeyboardButton('Jalali', callback_data='Jalali'))
        bot.send_message(
            message.chat.id, '\n'.join(
                ["Please choose your preferred calendar type to use in your tasks list. You can always change it later in /settings."]),
            reply_markup=markup)
        db.session.commit()
    else:
        bot.reply_to(
            message,
            'Please use /settings.')


@bot.message_handler(commands=['timezone'])
def set_timezone(message):
    cleanup(message)
    text= ["Below are some time zones you can choose from directly:",
    '',
    "<b>Don't see your time zone or not sure? Use /search.</b>"]
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if not user:
        user = User(chat_id = message.chat.id, status = wait_tz, date_joined=datetime.now())
        db.session.add(user)
    elif user and user.timezone:
        now = datetime.now()
        local_timezone = user.timezone
        local_now = now.astimezone(timezone(local_timezone))
        local_time = '{0:%H}:{0:%M}'.format(local_now)
        if user.calendar == 'Jalali':
            local_now = JalaliDate(local_now)
        text = [f'Your time zone is set to <b>{local_timezone}</b>.',
        f'{clock} ' + 'Current time: <b>{0:%B} {0.day}, '.format(local_now) + f'{local_time} </b>',
        ''] + text
        user.status = wait_tz
    else:
        user.status = wait_tz
    db.session.commit()
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton(f'{iran} Tehran', callback_data=tehran),
        InlineKeyboardButton(f'{turkey} Istanbul', callback_data=istanbul),
        InlineKeyboardButton(f'{france} Paris', callback_data=paris))
    markup.add(
        InlineKeyboardButton(f'{uk} London', callback_data=london),
        InlineKeyboardButton(f'{us} New York', callback_data=newyork),
        InlineKeyboardButton(f'{us} Chicago', callback_data=chicago))
    markup.add(
        InlineKeyboardButton(f'{canada} Edmonton', callback_data=edmonton),
        InlineKeyboardButton(f'{canada} Vancouver', callback_data=vancouver))

    bot.send_message(
        message.chat.id,
        '\n'.join(text),
        reply_markup=markup,
        parse_mode='HTML')


@bot.message_handler(commands=['search'])
def tz_search(message):
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if user and user.status == wait_tz:
        text = '\n'.join(
                ["Send the name of:",
                '',
                "<b>1- Your current city</b>",
                "or",
                "<b>2- Any other city/country obersving your time zone</b>.",
                '',
                f"{brhombus} Only your time zone label will be stored. Precisely, the value of 'TZ database name' column in <a href=\"https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List\">this table</a>."])

        bot.send_message(
            message.chat.id,
            text,
            disable_web_page_preview=True,
            parse_mode='HTML')


@bot.message_handler(commands=['purge'])
def purge(message):
    tasks = Task.query.filter_by(chat_id=message.chat.id).all()
    if tasks:
        for task in tasks:
            db.session.delete(task)
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if user:
        db.session.delete(user)
    db.session.commit()
    bot.reply_to(message, 'Purged!')


@bot.message_handler(func=lambda message: True, content_types=['text'])
def text(message):
    user = User.query.filter_by(chat_id=message.chat.id).first()
    if user:
        if user.status == wait_type:
            cleanup(message)
            bot.reply_to(message, 'Last operation was cancelled. Do you want to add a /new task?')
        elif user.status == wait_name:
            task = Task.query.filter_by(chat_id=message.chat.id, timestamp=None).first()
            task.name = message.text
            user.status = wait_date
            db.session.commit()
            bot.reply_to(message, '\n'.join(
                ['Now enter the deadline:',
                "Example: Oct 8 9:21"]))
        elif user.status == wait_date:
            user.status = idle
            task = Task.query.filter_by(chat_id=message.chat.id, timestamp=None).first()

            try:
                deadline = dateparser.parse(message.text, settings={"TIMEZONE": f"{user.timezone}", 'TO_TIMEZONE': 'UTC'})
                if not deadline:
                    deadline = JalaliCalendar(message.text).get_date().date_obj
                    user_timezone = timezone(user.timezone)
                    deadline = user_timezone.localize(deadline)
                    deadline = deadline.astimezone(timezone('Etc/UTC'))
                else:
                    year_in_text = re.search("[0-9]{4}", message.text)
                    if year_in_text is None:
                        deadline = deadline.replace(year=datetime.now().year)
                task.timestamp = deadline.timestamp()
                db.session.add(task)
                db.session.commit()
                bot.reply_to(message, '\n'.join(
                    ['Done!']))
            except:
                bot.reply_to(message, '\n'.join(
                    ['Invalid datetime format. Try again.',
                    "Example: Oct 8 9:21"]))
        elif user.status == wait_tz:
            try:
                g = geocoders.Nominatim(user_agent='MyTasks')
                cityinfo = g.geocode(message.text)
                lat = cityinfo[1][0]
                lng = cityinfo[1][1]

                tf = TimezoneFinder()
                user_timezone = tf.timezone_at(lng=lng, lat=lat)
                user.status = idle
                user.timezone = user_timezone
                db.session.commit()

                now = datetime.now()
                local_timezone = user_timezone
                local_now = now.astimezone(timezone(local_timezone))
                bot.send_message(
                    message.chat.id,
                    '\n'.join(
                        [f'Great! Your time zone is now set to <b>{local_timezone}</b>.',
                        f'{clock} ' + 'Current time: <b>{0:%H}:{0:%M}</b>'.format(local_now),
                        '',
                        'If this is not your local time, tap on /timezone and try again.']),
                    parse_mode='HTML')
            except:
                bot.send_message(message.chat.id, 'This is not a valid location.')
        elif message.text[0:7] == "/delete":
            try:
                task_id = int(message.text[8:])
                task = Task.query.filter_by(task_id=task_id, chat_id=message.chat.id).first()
                db.session.delete(task)
                db.session.commit()
                bot.reply_to(message, '\n'.join(
                ['Task was successfully deleted.',
                'Do you want to /see the updated list?']))
            except:
                bot.reply_to(message, '\n'.join(
                    ['Invalid delete command. Already deleted?']))
        elif user.status == idle:
            bot.reply_to(message, '\n'.join(
                    ['Are you trying to add a /new task?']))
