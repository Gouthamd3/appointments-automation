from flask import Flask, render_template, request, redirect, url_for
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# fix for websockets thing (idk why it breaks without this)
try:
    from websockets import client as ws_client
    if 'websockets.asyncio' not in sys.modules:
        sys.modules['websockets.asyncio'] = type(sys)('websockets.asyncio')
    if 'websockets.asyncio.client' not in sys.modules:
        sys.modules['websockets.asyncio.client'] = ws_client
except:
    pass

from supabase import create_client, Client
from twilio.rest import Client as TClient

# setup flask
app = Flask(__name__, template_folder='templates', static_folder='static')

# load env stuff
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
sb_url = os.environ.get("SUPABASE_URL")
sb_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(sb_url, sb_key)

# twilio setup
tw_client = TClient(
    os.environ.get("TWILIO_SID"),
    os.environ.get("TWILIO_AUTH_TOKEN")
)

def get_time_remaining(time_string):
    # calculates how much time is left until appointment
    try:
        appt_datetime = datetime.strptime(time_string, '%Y-%m-%dT%H:%M')
        current_time = datetime.now()
        
        if appt_datetime < current_time:
            return "Passed"
        
        time_diff = appt_datetime - current_time
        num_days = time_diff.days
        num_seconds = time_diff.seconds
        num_hours = num_seconds // 3600
        
        if num_days > 0:
            return f"{num_days}d {num_hours}h left"
        elif num_hours > 0:
            return f"{num_hours}h left"
        else:
            return "Less than 1h left!"
    except Exception as err:
        print(f"error calculating time: {err}")
        return "Unknown"


@app.route('/', methods=['GET'])
def index():
    msg = request.args.get('message')
    sort = request.args.get('sort', 'asc')
    
    appointments = []
    try:
        # get appointments from db
        resp = supabase.table('appointments').select('*').order('appointment_time', desc=(sort == 'desc')).execute()
        appointments = resp.data
        
        # add time remaining for each appt
        for a in appointments:
            a['time_left'] = get_time_remaining(a['appointment_time'])
            
    except Exception as ex:
        print(f"db error: {ex}")
        appointments = []

    return render_template('index.html', appointments=appointments, message=msg, current_sort=sort)


@app.route('/book', methods=['POST'])
def book_appointment():
    # form data
    customer_name = request.form.get('name')
    phone_num = request.form.get('phone')
    appt_time = request.form.get('time')
    
    sms_sent = False 
    result_message = ""

    # try to send sms
    try:
        msg_content = f"Hi {customer_name}, your appointment is confirmed for {appt_time.replace('T', ' ')}."
        tw_client.messages.create(
            body=msg_content,
            from_=os.environ.get("TWILIO_PHONE_NUMBER"),
            to=phone_num
        )
        sms_sent = True 
        result_message = "Appointment saved and message sent successfully!"
    except Exception as sms_err:
        print(f"sms error: {sms_err}")
        result_message = "Booked, but SMS failed (Invalid or unverified number)."

    # save to database
    try:
        supabase.table('appointments').insert({
            'name': customer_name,
            'phone': phone_num,
            'appointment_time': appt_time,
            'message_sent': sms_sent,
            'reminder_sent': False
        }).execute()
    except Exception as db_err:
        print(f"database error: {db_err}")
        result_message = "Database Error occurred."

    return redirect(url_for('index', message=result_message))


@app.route('/delete/<int:appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    # delete single appointment
    try:
        supabase.table('appointments').delete().eq('id', appointment_id).execute()
        msg = "Appointment deleted."
    except Exception as e:
        print(f"delete error: {e}")
        msg = "Error deleting appointment"
        
    return redirect(url_for('index', message=msg))


@app.route('/bulk_delete', methods=['POST'])
def bulk_delete():
    # delete multiple appointments
    ids_to_delete = request.form.getlist('appointment_ids')
    
    if ids_to_delete:
        try:
            supabase.table('appointments').delete().in_('id', ids_to_delete).execute()
            msg = f"{len(ids_to_delete)} appointments deleted."
        except Exception as e:
            print(f"bulk delete error: {e}")
            msg = "Error deleting appointments"
        return redirect(url_for('index', message=msg))
    
    return redirect(url_for('index'))


@app.route('/trigger-reminders', methods=['GET','POST'])
def trigger_reminders():
    # check for appointments that need reminders sent
    now = datetime.now()
    count = 0

    try:
        # get appointments without reminders
        resp = supabase.table('appointments').select('*').eq('reminder_sent', False).execute()
        appts = resp.data
        
        for appt in appts:
            try:
                appt_datetime = datetime.strptime(appt['appointment_time'], '%Y-%m-%dT%H:%M')
                seconds_until_appt = (appt_datetime - now).total_seconds()
                
                # if appointment is in the next hour
                if 0 < seconds_until_appt <= 3600:
                    reminder_msg = f"REMINDER: Hi {appt['name']}, your appointment is in less than 1 hour!"
                    tw_client.messages.create(
                        body=reminder_msg,
                        from_=os.environ.get("TWILIO_PHONE_NUMBER"),
                        to=appt['phone']
                    )
                    
                    # mark as sent in db
                    supabase.table('appointments').update({'reminder_sent': True}).eq('id', appt['id']).execute()
                    count += 1
                    print(f"reminder sent for ID: {appt['id']}")

            except Exception as loop_err:
                print(f"error for {appt['name']}: {loop_err}")
                
        msg = f"Scan complete: {count} reminders sent!"
        return redirect(url_for('index', message=msg))
    
    except Exception as main_err:
        print(f"reminder scan error: {main_err}")
        return redirect(url_for('index', message="Error processing reminders."))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
