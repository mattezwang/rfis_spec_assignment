## Title: Plant Care Tracker

# Problem
The problem is that two roommates are uncoordinated when caring for their plants. 

# Goals

G2: Track Watering Events (G2.1 Record Watering Events, G2.2 Identify Upcoming and Overdue Watering)

G3: Track Sunlight Exposure (G3.1 Track when plants are moved outside, G3.2 identify when plants should be brough inside)

G4: Coordinate Shared Plant Care (G4.1 Maintain shared care records, G4.2 Avoid duplicate or missed care activities)



# Requirements

# Plants
R1: A user can add a plant with a name and location
R2: A user can set a day interval for watering for each plant
R3: A user can set a plant's outside sun hourly time limit
R4: A user can edit a plant's schedule and details


# Watering

R5 (G2.1): A user can record when a plant was watered, and who did it
R6 (G2.2): For each plant, the application shows when it was last watered and next watering time based on its watering interval
R7 (G2.2): A plant that's watering time has passed is marked as overdue until someone records a watering for it
R8 (G2.2): A plant that has not been watering in the application is shown as needing to be watered


# Sunlight

R9 (G3.1): A user can record when a plant went outside, and who did it
R10 (G3.2): For each plant that is outside, the application shows when it should be brought back inside by the plant's outside interval
R11 (G3.2): A plant that's bring-inside time has passed it makred as overdue to bring inside until someone records that the plant was brought inside
R12 (G3.1): A user can record that a plant was brought back inside, which removes the outside and overdue mark


# Care
R13 (G4.1): Both roomates see the same information (plants, scehdules, history). A change made by one is visible to the other
R14 (G4.1): For each plant, the application shows who last watered it and when, and who last brought it outside and when
R15 (G4.1): A user can view a plant's care history (watering and outside history)
R16 (G4.2): If a user tries to water a plant that was recently brought outside, the app warns them to avoid watering it twice, but the user can bypass the warning


# Dashboard

R17: The applicaton has a dashboard that shows which plants need attention: overdue for watering, need watering today, plants currently outside, and plants that need to come in
R18: The most urgent items appear first and are visually distint
R19: The user can record a watering / plant movement from the dashboard


# Assumptions

- a login system is not needed this version for a two-person household
- Users enter all care information themselves, no automation


# Out of Scope

- Notifications or reminders (email, push, text)
- Calculating how much water / sunlight a plant needs
- Tracking other plant care needs, like fertilization
- Visual photos of plants
- Multiple households or user accounts with passwords
