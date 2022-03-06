# My Tasks: A Telegram Bot (Beta)
A Telegram bot for managing tasks with deadlines. (Link to bot: https://t.me/MyTasksRobot?start=start)

If you want to fork and make your own bot using this code, replace your information in the first part of the code encapsulated in "# To replace" labels.

## Changelog
### v0.4

Notification 2 hours or 24 hours prior to deadlines (Disabled by default)

### v0.3

Jalali calendar support in the Tasks List

New /settings command for all settings (excpet timezone)

Added option to hide the remaining time

### v0.2

Customized time zone

Rich text in several messages

### v0.1

Persian calendar support

Default timezone is now Asia/Tehran instead of UTC.

Most common datetime formats are now supported (thanks to dateparser).

## (Possibly) Upcoming Features
Persian localization

## Terms of Service & Privacy Policy
(Updated May 25, 2021)

**a)** It's not guaranteed that the bot will work properly. The results it provides, e.g. the remaining times, could be incorrect and its services might stop working at any time without prior notice. I will, however, try my best to fix the bugs and notify you beforehand whenever the bot will be unavailable.

**b)** This bot stores the following "Data" of its "Users" on a database, with no encryption (plain text):

1- Telegram User ID (A unique number for each Telegram user)

2- User-specified time zone (*Read below)

3- Date they first used the bot

4- Name of the tasks

5- Timestamp of the deadlines

*To display the remaining times for the tasks, user's current time zone is needed. For this purpose, users' time zones will be asked and saved, as provided by the user, according to the values in 'TZ database name' column in [this list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List). No exact location is collected. For example, for three users who send Amsterdam, Stockholm, and Paris as their current city, 'Europe/Paris' will be saved for all of them as their time zone.

The aforementioned Data is stored on https://pythonanywhere.com which is a free hosting website. Apart from this, I will not disclose your Data to any other third-party. By using the bot, however, you are also agreeing to pythonanywhere's data collection policy specified in their [Privacy Policy](https://www.pythonanywhere.com/privacy).

**c)** To prevent any harm, in case of incidents like data breach, it's best if you avoid including any sensitive information in the task names.

**d)** You'll be notified about any future updates to the Terms of Service and/or the Privacy Policy through the bot's chat with you, at least a week before they are effective. By continuing to use the bot after the provided date, you are agreeing to the updated Terms of Service and Privacy Policy.
