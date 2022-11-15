# gqrx-apscheduler
A python based application allowing to schedule commands to be sent to qgrx. 
For more info about gqrx refer to https://gqrx.dk/

## Installation
All you need is the single file **gqrx-apscheduler.py**. 
Copy this file to your computer. 
Make sure you have python installed. 

## Usage

### Create the schedule file
Together with the source files you will find a template called 
gqrx.toml which should simplify your first trials. 

A valid schedule file contains at least the following three configuration blocks
- **[connection-settings]**
- **[initial-setup]**
- as many you need of **[[task]]** blocks

In the **[connection-settings]** block you define how qgrx can be reached. 
```
[connection-settings]
    hostname = "localhost"
    port = 7356
```

The **[initial-setup]** is contains commands which are transmitted to 
gqrx at the moment the scheduler is started. In the example below the 
demodulation will be switched off and the DSP is stopped.
```
[initial-setup]
    commands=["M OFF", "U DSP 0"]
```
The real essence of configuration is sitting in the **[[task]]** blocks. 
Check the two files **qgrx.toml** and **test.toml** for examples and explanations. 

### Start the scheduler
Make sure:
- gqrx is running
- and the Remote Control Mode is enabled

Then start the scheduler with:
> python ./gqrx-adv-scheduler schedule-file.toml

