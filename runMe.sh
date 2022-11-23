# runMe - Configs
#
# 1 - Install requisites via pip
sudo pip install -r requirements.txt
#
# 2 - We use the viewconf tool to get Environment so we need to put these lines on the end
echo \#\#\#\#\# \"APP_SEND_INTERVAL_SEC\": _________________ == APP_SEND_INTERVAL_SEC >> ../../tools/viewconf/viewconf.c
echo \#\#\#\#\# \"APP_WARM_UP_PERIOD_SEC\": ________________ == APP_WARM_UP_PERIOD_SEC >> ../../tools/viewconf/viewconf.c
# Creating the empty files for web app.
touch COOJA.log
touch COOJA.testlog
