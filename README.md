# WhatsApp Appointment Reminder System

A serverless web application designed to handle appointment bookings and automate SMS/WhatsApp reminders. Built as a practical evaluation for Better Call Centers / El Paso Water Quality LLC.

## 🚀 Live Demo
https://appointments-automation.vercel.app/

## 📋 Overview
This project provides a seamless interface for booking appointments and a live dashboard for managing them. It focuses on a clean separation of concerns, utilizing Server-Side Rendering (SSR) via Python to ensure API keys and database credentials remain completely secure and hidden from the client browser.

### Key Features
- **Secure Booking:** Users enter a name, phone number, and appointment time.
- **Automated Messaging:** Instantly sends a confirmation SMS via Twilio upon booking.
- **Live Dashboard:** Displays all appointments pulled in real-time from Supabase.
- **Data Management:** Includes ascending/descending sorting and bulk deletion capabilities.
- **Bonus Challenge (1-Hour Reminders):** Implemented a background automation system using Vercel Cron Jobs to scan the database hourly and dispatch reminders for appointments happening within the next 60 minutes.

## 🛠️ Tech Stack
- **Frontend:** HTML5, CSS3 (Custom styling, CSS variables, `:has()` selectors for dynamic UI).
- **Backend:** Python (Flask) running as Vercel Serverless Functions.
- **Database:** Supabase (PostgreSQL).
- **Messaging Service:** Twilio API.
- **Hosting & Automation:** Vercel (Hosting, CI/CD, Cron Jobs).

## 🐛 Troubleshooting & Error Resolution: The Dependency Challenge
During deployment, the application encountered a critical build failure on Vercel followed by a `500 INTERNAL_SERVER_ERROR`. This was a complex case of "Dependency Hell" involving Python packages.

- **Architectural Strategy:** Deciding the optimal way to deploy a Python application on Vercel utilizing the `/api` folder structure for serverless functions rather than a continuously running server.
- **CSS Generation:** Generating modern, clean CSS (utilizing Flexbox, transitions, and CSS variables) to create a polished "SaaS" look without the overhead of heavy frameworks like Bootstrap or Tailwind.
- **Bonus Feature Logic:** Strategizing the best approach for the 1-hour reminder challenge, moving from a manual trigger button to a fully automated Cron Job using. https://console.cron-job.org/jobs
