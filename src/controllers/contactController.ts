import { Request, Response } from 'express';
import nodemailer from 'nodemailer';
import { Contact } from '../models/ContactModel';

export const sendEmail = async (req: Request, res: Response) => {
    const contact: Contact = req.body;
    // Send email using nodemailer
    // ...
    res.status(200).json({ message: 'Email sent successfully' });
};