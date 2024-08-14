# Stage 1: Build the Angular app
FROM node:18 as build-stage

# Set the working directory in the container
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy the Angular app code
COPY . .

# Build the app
RUN npm run build --prod

# Stage 2: Serve the app using Nginx
FROM nginx:alpine

# Copy the built Angular app from the previous stage to the Nginx web directory
COPY --from=build-stage /app/dist/frontend /usr/share/nginx/html

# Expose port 80 to the outside world
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
