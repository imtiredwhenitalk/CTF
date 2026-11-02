const express = require('express');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

const JWT_SECRET = 'secret123'; // Weak secret for CTF

app.get('/', (req, res) => {
    res.json({
        message: "Titan Admin API",
        auth_endpoint: "POST /login (guest/guest)",
        flag_endpoint: "GET /admin/flag (Requires role: internal_admin)"
    });
});

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    if (username === 'guest' && password === 'guest') {
        const token = jwt.sign({ username: 'guest', role: 'guest' }, JWT_SECRET, { expiresIn: '1h' });
        return res.json({ token });
    }
    res.status(401).json({ error: "Invalid credentials" });
});

app.get('/admin/flag', (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ error: "No token provided" });

    const token = authHeader.split(' ')[1];
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        if (decoded.role === 'internal_admin') {
            return res.json({ flag: "CTF{jwt_s3cr3ts_sh0uld_n3v3r_b3_w34k}" });
        }
        res.status(403).json({ error: "Forbidden. Requires role: internal_admin" });
    } catch (err) {
        res.status(400).json({ error: "Invalid token" });
    }
});

app.listen(3000, () => console.log('API listening on port 3000'));
