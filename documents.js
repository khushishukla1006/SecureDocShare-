const express = require('express');
const router = express.Router();
const Document = require('../models/Document');
const User = require('../models/User');
const multer = require('multer');
const path = require('path');

// Configure multer for file upload
const storage = multer.diskStorage({
    destination: './uploads/',
    filename: function(req, file, cb) {
        cb(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname));
    }
});

const upload = multer({ storage: storage });

// Upload document
router.post('/upload', upload.single('file'), async (req, res) => {
    try {
        const { title } = req.body;
        const userId = req.user.id;

        // Generate keys
        const highPriorityKey = require('crypto').randomBytes(16).toString('hex');
        const lowPriorityKey = require('crypto').randomBytes(16).toString('hex');

        // Create document
        const document = new Document({
            title,
            file: req.file.path,
            owner: userId,
            highPriorityKey,
            lowPriorityKey
        });

        await document.save();

        res.status(201).json({
            documentId: document._id,
            highPriorityKey,
            lowPriorityKey
        });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// View document
router.get('/view/:documentId/:key', async (req, res) => {
    try {
        const { documentId, key } = req.params;
        const document = await Document.findOne({ _id: documentId });

        if (!document) {
            return res.status(404).json({ message: 'Document not found' });
        }

        // Check if document is active
        if (!document.isActive) {
            return res.status(403).json({ message: 'Access revoked' });
        }

        // Check if key is valid
        if (key !== document.highPriorityKey && key !== document.lowPriorityKey) {
            return res.status(403).json({ message: 'Invalid key' });
        }

        // Log access
        document.viewers.push({
            viewerId: req.user ? req.user.id : null,
            lastAccessed: new Date(),
            ip: req.ip
        });

        await document.save();

        // Serve the document with restricted access
        res.sendFile(document.file);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Revoke access
router.post('/revoke/:documentId', async (req, res) => {
    try {
        const { documentId } = req.params;
        const document = await Document.findOne({ _id: documentId, owner: req.user.id });

        if (!document) {
            return res.status(404).json({ message: 'Document not found' });
        }

        document.isActive = false;
        await document.save();

        res.json({ message: 'Access revoked successfully' });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

module.exports = router;
