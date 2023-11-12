import { Request, Response } from 'express';
import { Email } from '../models/EmailModel';
import { db } from '../config/database';
import { FieldPacket, RowDataPacket } from 'mysql2';

export const saveEmail = async (req: Request, res: Response) => {
    const email: Email = req.body;

    if (!email.address) {
        return res.status(400).json({ message: 'Email address is required' });
    }

    try {
        // Check if email already exists
        const checkQuery = 'SELECT * FROM emails WHERE address = ?';
        const [rows] = await db.execute(checkQuery, [email.address]) as [RowDataPacket[], FieldPacket[]];

        if ((rows as RowDataPacket[]).length > 0) {
            return res.status(409).json({ message: 'Email already exists' });
        }

        // Insert email into the database
        const insertQuery = 'INSERT INTO emails (address) VALUES (?)';
        const [insertResult] = await db.execute(insertQuery, [email.address]) as [RowDataPacket[], FieldPacket[]];

        res.status(200).json({ message: 'Email saved successfully', data: insertResult });
    } catch (error) {
        console.error('Error saving email:', error);
        res.status(500).json({ message: 'Error saving email' });
    }
};