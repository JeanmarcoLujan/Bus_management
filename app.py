import os
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import dotenv


dotenv.load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="Buus",
    page_icon="🚌",
    initial_sidebar_state="expanded",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None,
    }
)


# Conectar a la base de datos MongoDB
client = MongoClient(os.environ['MI_MONGODB'])
db = client["bus_management"]
buses_collection = db["buses"]
schedules_collection = db["schedules"]
bookings_collection = db["bookings"]

# Funciones para manejar los datos
def get_buses():
    return list(buses_collection.find({}))

def get_schedules(bus_id):
    return list(schedules_collection.find({"bus_id": bus_id}))

def book_seat(schedule_id, seat_number, passenger_info):
    booking = {
        "schedule_id": schedule_id,
        "seat_number": seat_number,
        "passenger_info": passenger_info
    }
    bookings_collection.insert_one(booking)

def cancel_seat(schedule_id, seat_number):
    bookings_collection.delete_one({"schedule_id": schedule_id, "seat_number": seat_number})

def get_bookings(schedule_id):
    return list(bookings_collection.find({"schedule_id": schedule_id}))

def add_bus(bus_number, capacity):
    bus = {"bus_number": bus_number, "capacity": capacity}
    buses_collection.insert_one(bus)

def update_bus(bus_id, bus_number, capacity):
    buses_collection.update_one({"_id": bus_id}, {"$set": {"bus_number": bus_number, "capacity": capacity}})

def delete_bus(bus_id):
    buses_collection.delete_one({"_id": bus_id})
    schedules_collection.delete_many({"bus_id": bus_id})
    bookings_collection.delete_many({"schedule_id": {"$in": [s["_id"] for s in get_schedules(bus_id)]}})

def add_schedule(bus_id, departure_time, arrival_time, date):
    schedule = {
        "bus_id": bus_id,
        "departure_time": departure_time,
        "arrival_time": arrival_time,
        "date": date
    }
    schedules_collection.insert_one(schedule)

def update_schedule(schedule_id, departure_time, arrival_time, date):
    schedules_collection.update_one({"_id": schedule_id}, {"$set": {"departure_time": departure_time, "arrival_time": arrival_time, "date": date}})

def delete_schedule(schedule_id):
    schedules_collection.delete_one({"_id": schedule_id})
    bookings_collection.delete_many({"schedule_id": schedule_id})

def get_passengers(bus_id, schedule_id=None):
    if schedule_id:
        bookings = get_bookings(schedule_id)
        schedule = schedules_collection.find_one({"_id": schedule_id})
        passengers = [{
            "schedule_date": schedule["date"],
            "departure_time": schedule["departure_time"],
            "seat_number": booking["seat_number"],
            "name": booking["passenger_info"]["name"],
            "age": booking["passenger_info"]["age"],
            "gender": booking["passenger_info"]["gender"],
            "contact_info": booking["passenger_info"]["contact_info"]
        } for booking in bookings]
    else:
        schedules = get_schedules(bus_id)
        passengers = []
        for schedule in schedules:
            bookings = get_bookings(schedule["_id"])
            for booking in bookings:
                passengers.append({
                    "schedule_date": schedule["date"],
                    "departure_time": schedule["departure_time"],
                    "seat_number": booking["seat_number"],
                    "name": booking["passenger_info"]["name"],
                    "age": booking["passenger_info"]["age"],
                    "gender": booking["passenger_info"]["gender"],
                    "contact_info": booking["passenger_info"]["contact_info"]
                })
    return passengers

# Inicializar la sesión de estado
if 'refresh' not in st.session_state:
    st.session_state['refresh'] = False

# Interfaz de usuario con navegación
st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a", ["Registro de Buses y Horarios", "Ver y Reservar Asientos", "Ver Pasajeros"])

if page == "Registro de Buses y Horarios":
    st.title("Registro de Buses y Horarios")
    
    # Sección para registrar y actualizar buses
    st.header("Registrar o Actualizar Bus")
    buses = get_buses()
    bus_options = {bus["bus_number"]: bus["_id"] for bus in buses}
    selected_bus = st.selectbox("Selecciona un bus para actualizar o eliminar", ["Nuevo Bus"] + list(bus_options.keys()))
    
    if selected_bus == "Nuevo Bus":
        bus_number = st.text_input("Número del bus")
        capacity = st.number_input("Capacidad", min_value=1)
        submit_bus = st.button(label='Registrar Bus')
        if submit_bus:
            add_bus(bus_number, capacity)
            st.success("Bus registrado con éxito")
    else:
        bus_id = bus_options[selected_bus]
        bus = next(bus for bus in buses if bus["_id"] == bus_id)
        bus_number = st.text_input("Número del bus", value=bus["bus_number"])
        capacity = st.number_input("Capacidad", min_value=1, value=bus["capacity"])
        update_bus_button = st.button(label='Actualizar Bus')
        delete_bus_button = st.button(label='Eliminar Bus')
        if update_bus_button:
            update_bus(bus_id, bus_number, capacity)
            st.success("Bus actualizado con éxito")
        if delete_bus_button:
            delete_bus(bus_id)
            st.success("Bus eliminado con éxito")
    
    # Sección para registrar y actualizar horarios
    st.header("Registrar o Actualizar Horario")
    if selected_bus != "Nuevo Bus":
        schedules = get_schedules(bus_id)
        schedule_options = {f"{s['date']} - {s['departure_time']}": s["_id"] for s in schedules}
        selected_schedule = st.selectbox("Selecciona un horario para actualizar o eliminar", ["Nuevo Horario"] + list(schedule_options.keys()))
        
        if selected_schedule == "Nuevo Horario":
            departure_time = st.text_input("Hora de salida (HH:MM)", value="08:00")
            arrival_time = st.text_input("Hora de llegada (HH:MM)", value="12:00")
            date = st.date_input("Fecha")
            submit_schedule = st.button(label='Registrar Horario')
            if submit_schedule:
                add_schedule(bus_id, departure_time, arrival_time, str(date))
                st.success("Horario registrado con éxito")
        else:
            schedule_id = schedule_options[selected_schedule]
            schedule = next(s for s in schedules if s["_id"] == schedule_id)
            departure_time = st.text_input("Hora de salida (HH:MM)", value=schedule["departure_time"])
            arrival_time = st.text_input("Hora de llegada (HH:MM)", value=schedule["arrival_time"])
            date = st.date_input("Fecha", value=pd.to_datetime(schedule["date"]))
            update_schedule_button = st.button(label='Actualizar Horario')
            delete_schedule_button = st.button(label='Eliminar Horario')
            if update_schedule_button:
                update_schedule(schedule_id, departure_time, arrival_time, str(date))
                st.success("Horario actualizado con éxito")
            if delete_schedule_button:
                delete_schedule(schedule_id)
                st.success("Horario eliminado con éxito")

elif page == "Ver y Reservar Asientos":
    st.title("Gestión de Pasajes de Bus - Ver y Reservar Asientos")

    st.header("Ver y Reservar Asientos")

    buses = get_buses()
    bus_options = {bus["bus_number"]: bus["_id"] for bus in buses}
    bus_choice = st.selectbox("Selecciona un bus", list(bus_options.keys()), key="ver_bus")

    if bus_choice:
        bus_id = bus_options[bus_choice]
        schedules = get_schedules(bus_id)
        schedule_options = {f"{s['date']} - {s['departure_time']}": s["_id"] for s in schedules}
        schedule_choice = st.selectbox("Selecciona un horario", list(schedule_options.keys()), key="ver_horario")

        if schedule_choice:
            schedule_id = schedule_options[schedule_choice]
            bus = next(bus for bus in buses if bus["_id"] == bus_id)
            booked_seats = {b["seat_number"] for b in get_bookings(schedule_id)}

            st.write(f"Bus {bus['bus_number']} - Asientos (Capacidad: {bus['capacity']})")
            seat_layout = []
            for seat in range(1, bus["capacity"] + 1):
                if seat in booked_seats:
                    seat_layout.append(f"🚫 {seat}")
                else:
                    seat_layout.append(f"✅ {seat}")

            # Mostrar el estado de los asientos
            st.write(" ".join(seat_layout))

            # Botón para refrescar manualmente la lista de asientos
            if st.button("Actualizar estado de los asientos"):
                st.session_state['refresh'] = not st.session_state['refresh']
                #st.experimental_rerun()

            # Seleccionar asiento para reservar
            available_seats = [seat for seat in range(1, bus["capacity"] + 1) if seat not in booked_seats]
            seat_to_book = st.selectbox("Selecciona un asiento para reservar", available_seats)
            name = st.text_input("Nombre del pasajero", key="reserva_nombre")
            age = st.number_input("Edad", min_value=1, key="reserva_edad")
            gender = st.selectbox("Género", ["Masculino", "Femenino", "Otro"], key="reserva_genero")
            contact_info = st.text_input("Información de contacto", key="reserva_contacto")

            if st.button("Reservar asiento", key="reserva_asiento"):
                passenger_info = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "contact_info": contact_info
                }
                book_seat(schedule_id, seat_to_book, passenger_info)
                st.success("Asiento reservado con éxito")
                st.session_state['refresh'] = not st.session_state['refresh']
                #st.experimental_rerun()

            # Seleccionar asiento para cancelar
            if booked_seats:
                seat_to_cancel = st.selectbox("Selecciona un asiento para liberar", list(booked_seats), key="cancelar_asiento")
                if st.button("Liberar asiento", key="liberar_asiento"):
                    cancel_seat(schedule_id, seat_to_cancel)
                    st.success("Asiento liberado con éxito")
                    st.session_state['refresh'] = not st.session_state['refresh']
                    #st.experimental_rerun()

elif page == "Ver Pasajeros":
    st.title("Ver Pasajeros por Bus")

    st.header("Selecciona un Bus y Horario")
    buses = get_buses()
    bus_options = {bus["bus_number"]: bus["_id"] for bus in buses}
    bus_choice = st.selectbox("Selecciona un bus", list(bus_options.keys()), key="ver_bus_pasajeros")

    if bus_choice:
        bus_id = bus_options[bus_choice]
        schedules = get_schedules(bus_id)
        schedule_options = {f"{s['date']} - {s['departure_time']}": s["_id"] for s in schedules}
        schedule_choice = st.selectbox("Selecciona un horario", list(schedule_options.keys()), key="ver_horario_pasajeros")

        if schedule_choice:
            schedule_id = schedule_options[schedule_choice]
            passengers = get_passengers(bus_id, schedule_id)

            if passengers:
                df_passengers = pd.DataFrame(passengers)
                st.dataframe(df_passengers)
            else:
                st.write("No hay pasajeros registrados para este horario.")
