const axios = require('axios');

async function isLocalStackReady() {
    try {
        const response = await axios.get('http://host.docker.internal:4566/health');
        return response.data.services.s3 === 'running';
    } catch (error) {
        return false;
    }
}

async function waitForLocalStack() {
    const maxRetries = 10;
    const delay = 3000; // 3 seconds

    for (let i = 0; i < maxRetries; i++) {
        if (await isLocalStackReady()) {
            console.log('LocalStack is ready');
            return;
        }
        console.log('Waiting for LocalStack to be ready...');
        await new Promise(resolve => setTimeout(resolve, delay));
    }
    throw new Error('LocalStack did not start in time');
}

before(async function() {
    this.timeout(60000); // Increase timeout for setup
    await waitForLocalStack();
});

function newFunction() {
    // new functionality here
}

// ...existing code...
