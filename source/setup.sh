#!/bin/sh

# PATCH MINION - CENTOS MACHINE (TESTED)

# INSTALLING PATCH-MINION DEPENDENCIES
# Installing virtual env
echo "Installing virtualenv"
yum -y install python-virtualenv
# Creating virtual environment of python
echo "Creating virtualenv -- env"
virtualenv --distribute  $(pwd)/env
# Activating environment
echo "Created"
echo "Activating env"
source $(pwd)/env/bin/activate
cd $(pwd)
echo "Installing pip dependencies"
pip install --find-links="./" -r requires.txt
deactivate
echo "Finished - dependencies"

cat > $(pwd)/minion.sh << EOF
#!/bin/sh
source $(pwd)/env/bin/activate
start()
{
$(pwd)/env/bin/python app.py -p8082
}
start
EOF
chmod +x $(pwd)/minion.sh

# Setting up service 
echo "Setting up service for patch-minon"
cp $(pwd)/patch-minion.service /etc/systemd/system/patch-minion.service
systemctl enable patch-minion.service
systemctl start patch-minion.service
systemctl status patch-minion.service

echo ""
echo " - COMPLETED - "
echo ""
echo " To verify - open web browser with http://localhost:8082"

