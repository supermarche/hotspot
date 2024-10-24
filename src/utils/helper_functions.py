import datetime


def normalize_to_weeks(date_range):
    # Parse the start and end date
    start_date = datetime.datetime.strptime(date_range[0], '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(date_range[1], '%Y-%m-%d').date()

    # Function to adjust date to the previous Monday
    def to_previous_monday(date):
        return date - datetime.timedelta(days=date.weekday())

    # Function to adjust date to the next Sunday
    def to_next_sunday(date):
        return date + datetime.timedelta(days=(6 - date.weekday()))

    # Adjust the start date to the previous Monday and the end date to the next Sunday
    normalized_start = to_previous_monday(start_date)
    normalized_end = to_next_sunday(end_date)

    # List to store the result of weeks
    weeks = []

    # Create a loop that iterates through each week
    current_week_start = normalized_start
    while current_week_start <= normalized_end:
        current_week_end = current_week_start + datetime.timedelta(days=6)
        weeks.append((current_week_start, current_week_end))

        # Move to the next week
        current_week_start = current_week_start + datetime.timedelta(weeks=1)

    return weeks
