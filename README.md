# Open Devin Teams Bot

This Teams Bot is a simple bot that works with [Open Devin](https://github.com/OpenDevin/OpenDevin). This integration demonstrates the Open Devin worker integrated inside your Teams ecosystem where 
* you can interact with the AI agent where you work
* start long running complex tasks that it can do asyncronously
* get notifications when it needs something
* you can open the app to check how it's making progress on the tasks you've assigned it

![Screenshot of OpenDevin working inside Microsoft Teams](./docs/Screenshot%20of%20Teams.png)

---

Open Devin as it is, is an all-encompassing project. It contains the backend and frontend.
In this project, I tried to integrate the project with Microsoft Teams. It uses a [fork](https://github.com/heyitsaamir/OpenDevin) of Open Devin which contains two major modifications:
1. It removes the chat-pane from the frontend.
2. It modifies the backend such that socket messages are broadcasted to multiple frontends.
3. Enables the ability for the backend to ask the user questions

With the above changes, I created this bot ([originally](https://github.com/heyitsaamir/Open-Devin-Teams-Bot) written in javascript) which:
* Uses Microsoft Team's Tabs to display the Open Devin frontend (sans chat-pane).
* Uses the chat-pane in Teams to send messages to this Bot, which in turn sends the message to the Open Devin backend.

## Demo
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/beaO3s35Eq0/0.jpg)](https://www.youtube.com/watch?v=beaO3s35Eq0)
