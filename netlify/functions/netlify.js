// This file is just a placeholder to ensure Netlify recognizes the functions directory
exports.handler = async function(event, context) {
  return {
    statusCode: 200,
    body: JSON.stringify({ message: "Netlify Functions are working!" })
  };
};
