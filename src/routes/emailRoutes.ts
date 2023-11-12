import express from 'express';
import * as emailController from '../controllers/emailController';

const router = express.Router();

router.post('/save', emailController.saveEmail);

export default router;