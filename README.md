🚦 SmartTraffic Vision

AI-Powered Traffic Violation Detection System

📌 Overview

SmartTraffic Vision is a group project developed as part of the ICS2313: Software Testing & Quality Assurance course at Jomo Kenyatta University of Agriculture and Technology.

The system uses Artificial Intelligence (AI) and Computer Vision to automatically detect traffic violations from CCTV video streams. Instead of relying on human monitoring (which gets tired, distracted, or bored), this system works 24/7 without blinking.

👥 Team Members

Brian Kipkirui
Micah Sagero
John Nyongesa
Ian Mandila

🎯 Project Objective

To design an automated system that:

Detects traffic violations in real-time
Captures visual evidence (images + video clips)
Stores and organizes violation data
Provides reports for traffic authorities

🧠 Key Features

🚘 Vehicle Detection

Uses the YOLO (You Only Look Once) deep learning model
Identifies vehicles (cars, buses, trucks, motorcycles) in video frames

🎯 Object Tracking

Tracks vehicles across multiple frames
Enables movement analysis and behavior detection

🚨 Violation Detection

Detects two main violations:

Signal Jumping (running red lights)
Wrong-Way Driving

📸 Evidence Capture

Automatically saves:
Images
Short video clips
Links evidence to violation records

🔔 Alert System

Notifies authorities instantly when a violation occurs

📊 Reports & Analytics

Daily, weekly, and monthly reports
Violation trends and hotspot identification

🗄️ System Architecture

📂 Core Data Entities
Vehicle – Detected vehicles and tracking info
Violation – Type, time, and location
Camera – CCTV source data
Evidence – Images and video clips
User – Traffic officers and admins

🔗 Relationships

One camera → many vehicles
One vehicle → multiple violations
One violation → multiple evidence records
Users → review and manage violations

This structured design ensures efficient storage and retrieval of traffic data .

⚙️ System Workflow

Video Acquisition – CCTV feeds captured continuously
Vehicle Detection – AI model detects vehicles
Tracking – Movement monitored across frames
Violation Analysis – Rules applied to detect infractions
Alert Generation – System flags violations
Evidence Storage – Media saved in database
Report Generation – Insights provided to authorities

🖥️ User Interfaces

🔐 Login Interface – Secure authentication
📊 Dashboard – Real-time stats and alerts
🔍 Violation Review Panel – View evidence and verify detections
🎥 Camera Management – Add/remove/configure cameras
📈 Reports Module – Generate analytical reports

🧰 Technologies Used

Artificial Intelligence (AI)
Computer Vision
Deep Learning (YOLO)
Database Systems
CCTV Video Processing

🚀 Future Improvements

License plate recognition (ANPR)
Integration with smart city systems
Additional violation types (speeding, illegal parking)
Real-time enforcement integration (fines, notifications)

📌 Conclusion

SmartTraffic Vision demonstrates how AI can replace manual traffic monitoring with an intelligent, scalable system. It improves enforcement efficiency, reduces human error, and supports data-driven decision-making for safer roads
