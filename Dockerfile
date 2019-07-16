# base image
FROM continuumio/miniconda3

# set partition and working directory
WORKDIR /data

# install python libraries
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r /tmp/requirements.txt

# install jupyter extensions
# RUN python3 -m pip install jupyter_contrib_nbextensions
# RUN jupyter contrib nbextension install --user

# container entry point
# ENTRYPOINT ["/bin/bash"]
