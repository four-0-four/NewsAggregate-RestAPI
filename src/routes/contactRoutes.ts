import express from 'express';
import * as contactController from '../controllers/contactController';

const router = express.Router();

router.post('/send', contactController.sendEmail);

export default router;