# Netlify Functions

This directory contains Netlify Functions used to proxy requests to the Render backend.

## Functions

### proxy.js

This function proxies requests from the Netlify frontend to the Render backend. It handles:

- All HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
- JSON data
- Form data
- File uploads (multipart/form-data)

#### How it works

1. The function receives a request from the frontend
2. It extracts the path and query parameters
3. It constructs a URL to the Render backend
4. It forwards the request to the Render backend
5. It returns the response from the Render backend to the frontend

#### File Upload Handling

File uploads are handled using the `busboy` library to parse multipart/form-data requests. The function:

1. Parses the multipart/form-data request
2. Extracts the files and fields
3. Creates a new FormData object
4. Adds the files and fields to the FormData object
5. Sends the FormData object to the Render backend

#### Limitations

- File size is limited to 50MB
- Number of files is limited to 5
- Number of fields is limited to 10
- Field size is limited to 10MB
- Request timeout is set to 30 seconds

### test.js

This is a simple test function that returns a JSON response with information about the request. It's used to test if Netlify Functions are working correctly.

## Troubleshooting

If you encounter issues with the proxy function:

1. Check the Netlify function logs in the Netlify dashboard
2. Make sure the Render backend is running and accessible
3. Check if the file size is within the limits
4. Try using the Simple Upload Test page with a small file
5. Check if the request is timing out (30 seconds limit)

## Dependencies

The proxy function depends on the following npm packages:

- `node-fetch`: For making HTTP requests to the Render backend
- `form-data`: For creating multipart/form-data requests
- `busboy`: For parsing multipart/form-data requests

These dependencies are installed via the root package.json file.
