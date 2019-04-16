# climateAutomation
Automating climate control using a raspberry pi with openhab, influxDB, MQTT and python.
Below a brief overview of the components in the project are shown.
![alt text](https://github.com/sorenmc/climateAutomation/blob/master/ArchitectureCorrect.png "Architecture of project")

The code in this repository is for the raspberry pi's which serve as a hub in the climate automation. These hubs store climate data like humidity, temperature and CO2 levels in a room in a influxDB installed on the raspberry pi. Every hour this data is sent over MQTT and deleted from the influxDB. The hub can also be controlled over MQTT by using a website. 
