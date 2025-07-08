# Stage 1: Build the Angular app
FROM node:18 as build-stage

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (if present)
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the Angular app source code
COPY . .

# Build the Angular app using npx to avoid global CLI issues
RUN npx ng build --configuration production

# Stage 2: Serve the app using Nginx
FROM nginx:alpine

# Copy the built Angular app from the previous stage
COPY --from=build-stage /app/dist/frontend /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 to the outside world
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
