import 'reflect-metadata';
import express from 'express';
import bodyParser from 'body-parser';
import { AppDataSource } from './data-source';
import emailRoutes from './routes/emailRoutes';
import contactRoutes from './routes/contactRoutes';

const app = express();
app.use(bodyParser.json());

app.use('/api/email', emailRoutes);
app.use('/api/contact', contactRoutes);

AppDataSource.initialize().then(async () => {
    console.log('Data Source has been initialized!');
    app.listen(3000, () => {
        console.log('Server running on port 3000');
    });
}).catch((error) => console.error('Error during Data Source initialization', error));
