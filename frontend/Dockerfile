FROM node:21.7.1-alpine3.19

ARG VUE_APP_BACKEND_URL
ENV VUE_APP_BACKEND_URL=$VUE_APP_BACKEND_URL

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

#RUN apk add python make g++

COPY ./package.json /app/package.json
# COPY ./package-lock.json /app/package-lock.json
RUN npm install
# RUN npm install @vue/cli -g
RUN npm i --package-lock-only

COPY . /app

CMD npm run dev
