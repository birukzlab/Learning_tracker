from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.errors import HttpError
import logging


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1Jx0h02X3ukJA4pIJocRyqQhBoj383ivPW4rumLqWqUs'
RANGE_NAME = 'Sheet1!A2:D'
'''
creds = Credentials.from_service_account_file('utils/credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)

workbook = client.open_by_key(SPREADSHEET_ID)

sheets = workbook.worksheets()
print(sheets)
'''


PLAN_SHEET_NAME = 'Sheet1'
TIMER_SHEET_NAME = 'Sheet2'

logging.basicConfig(level=logging.DEBUG)

def get_service():
    try:
        creds = Credentials.from_service_account_file('utils/credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        logging.error(f"Error getting Google Sheets service: {e}")
        return None

def ensure_sheets_exist():
    try:
        service = get_service()
        if not service:
            return None
        sheet = service.spreadsheets()
        # Get the current sheets
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])

        sheet_names = [s['properties']['title'] for s in sheets]

        # Create the plan sheet if it doesn't exist
        if PLAN_SHEET_NAME not in sheet_names:
            requests = [
                {
                    'addSheet': {
                        'properties': {
                            'title': PLAN_SHEET_NAME
                        }
                    }
                }
            ]
            body = {
                'requests': requests
            }
            sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

            # Add headers to the plan sheet
            headers = [['Subject', 'Days', 'Hours per Day', 'Total Hours per Day', 'Total Hours per Month']]
            body = {'values': headers}
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, range=f'{PLAN_SHEET_NAME}!A2:E',
                valueInputOption='RAW', body=body).execute()

        # Create the timer sheet if it doesn't exist
        if TIMER_SHEET_NAME not in sheet_names:
            requests = [
                {
                    'addSheet': {
                        'properties': {
                            'title': TIMER_SHEET_NAME
                        }
                    }
                }
            ]
            body = {
                'requests': requests
            }
            sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

            # Add headers to the timer sheet
            headers = [['Subject', 'Daily Hours', 'Rolling Total']]
            body = {'values': headers}
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, range=f'{TIMER_SHEET_NAME}!A2:D',
                valueInputOption='RAW', body=body).execute()
    except Exception as e:
        logging.error(f"Error ensuring sheets exist: {e}")

def read_plan_data():
    try:
        service = get_service()
        if not service:
            return []
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{PLAN_SHEET_NAME}!A2:E').execute()
        return result.get('values', [])
    except Exception as e:
        logging.error(f"Error reading plan data from Google Sheets: {e}")
        return []

def write_plan_data(data):
    try:
        service = get_service()
        if not service:
            return None
        sheet = service.spreadsheets()
        # First, read the existing data
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{PLAN_SHEET_NAME}!A2:E').execute()
        existing_data = result.get('values', [])
        
        # Combine existing data with new data
        combined_data = existing_data + data
        
        # Write combined data back to the sheet
        body = {'values': combined_data}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=f'{PLAN_SHEET_NAME}!A2:E',
            valueInputOption='RAW', body=body).execute()
        return result
    except Exception as e:
        logging.error(f"Error writing plan data to Google Sheets: {e}")
        return None

def read_timer_data():
    try:
        service = get_service()
        if not service:
            return []
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{TIMER_SHEET_NAME}!A2:D').execute()
        return result.get('values', [])
    except Exception as e:
        logging.error(f"Error reading timer data from Google Sheets: {e}")
        return []

def log_daily_time(subject, daily_elapsed):
    try:
        service = get_service()
        if not service:
            return False
        sheet = service.spreadsheets()
        
        # Read current data
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{TIMER_SHEET_NAME}!A2:D').execute()
        values = result.get('values', [])
        
        logging.debug(f"Current timer values: {values}")

        # Find the row index of the subject to update
        for i, row in enumerate(values):
            if row[0] == subject:
                previous_daily = float(row[2]) if row[2] else 0
                rolling_total = float(row[3]) if row[3] else 0
                
                new_daily = previous_daily + daily_elapsed
                new_rolling_total = rolling_total + daily_elapsed
                
                values[i][2] = str(new_daily)
                values[i][3] = str(new_rolling_total)
                break
        else:
            # If the subject is not found, add a new row
            values.append([subject, '', str(daily_elapsed), str(daily_elapsed)])
        
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=f'{TIMER_SHEET_NAME}!A2:D',
            valueInputOption='RAW', body=body).execute()
        
        logging.debug(f"Update result: {result}")
        return True
    except Exception as e:
        logging.error(f"Error logging time to Google Sheets: {e}")
        return False

