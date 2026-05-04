FROM ubuntu:24.04 AS base

ENV DEBIAN_FRONTEND="noninteractive" TZ="America/New_York"
RUN apt-get update -y && apt-get install -y python3-dev python3-pip git unzip python3-tk libxml2-dev libxslt1-dev

ENV PIP_BREAK_SYSTEM_PACKAGES=1
# RUN  python3 -m pip install --upgrade pip

WORKDIR /validationTool
RUN git clone -b validation https://github.com/liuji1031/pycrate.git
RUN cd /validationTool/pycrate && python3 -m pip install -e .

COPY requirements.txt /validationTool/requirements.txt
RUN pip3 install -r requirements.txt

# install wheel for j2735 module
ARG WHEEL_FILE="j2735_202409-0.1.0-py3-none-any.whl"
COPY ./src/wheels/${WHEEL_FILE} /validationTool/
RUN pip3 install /validationTool/${WHEEL_FILE} && rm /validationTool/${WHEEL_FILE}


FROM base AS prod

COPY . /validationTool

ENTRYPOINT [ "python3" ]
CMD [ "validationTool.py" ]

FROM base AS dev

ARG USERNAME=devuser
ARG UID=1000
ARG GID=${UID}

# Create new user and home directory
RUN (userdel -r $(getent passwd $UID | cut -d: -f1) || true) && \
    (groupdel $(getent group $GID | cut -d: -f1) || true) && \
    groupadd --gid $GID $USERNAME \
    && useradd --uid ${UID} --gid ${GID} --create-home ${USERNAME} \
    # && echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
    # && chmod 0440 /etc/sudoers.d/${USERNAME} \
    && mkdir -p /home/${USERNAME} \
    && chown -R ${UID}:${GID} /home/${USERNAME}

RUN pip3 install ipykernel ipython

RUN chown -R ${UID}:${GID} /validationTool/
USER ${USERNAME}

ENTRYPOINT [ "sleep", "infinity" ]
