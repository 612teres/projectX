from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from flask import current_app, url_for
from app.models import CalendarEvent
from app import db
import os

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']

    @staticmethod
    def create_flow():
        return Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=GoogleCalendarService.SCOPES,
            redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
        )

    @staticmethod
    def build_credentials(flow, authorization_response):
        flow.fetch_token(authorization_response=authorization_response)
        return flow.credentials

    @staticmethod
    def create_service(credentials):
        return build('calendar', 'v3', credentials=credentials)

    @staticmethod
    def sync_events(service, user_id):
        # Get events from Google Calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=datetime.utcnow().isoformat() + 'Z',
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Sync with local database
        for event in events:
            existing_event = CalendarEvent.query.filter_by(
                google_event_id=event['id'],
                user_id=user_id
            ).first()

            if not existing_event:
                new_event = CalendarEvent(
                    google_event_id=event['id'],
                    title=event['summary'],
                    description=event.get('description', ''),
                    start_time=parse(event['start'].get('dateTime', event['start'].get('date'))),
                    end_time=parse(event['end'].get('dateTime', event['end'].get('date'))),
                    user_id=user_id
                )
                db.session.add(new_event)

        db.session.commit()

    @staticmethod
    def create_event(service, event_data):
        event = service.events().insert(
            calendarId='primary',
            body={
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end_time'].isoformat(),
                    'timeZone': 'UTC',
                }
            }
        ).execute()
        return event 