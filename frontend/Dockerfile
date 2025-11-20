FROM node:21.7.1-bullseye

ARG VITE_APP_BACKEND_URL
ENV VITE_APP_BACKEND_URL=$VITE_APP_BACKEND_URL

ARG VUE_APP_IS_DEMO
ENV VUE_APP_IS_DEMO=$VUE_APP_IS_DEMO

WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

#RUN apk add python make g++

COPY ./package.json /app/package.json
COPY ./package-lock.json /app/package-lock.json
RUN npm install
# RUN npm install @vue/cli -g

COPY . /app
# RUN rm -rf app/node_modules/.vite

#CMD npm run dev
