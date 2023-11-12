import mysql from 'mysql2';

const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASS || 's1i1n1a1',
    database: process.env.DB_NAME || 'mydb',
    port: Number(process.env.DB_PORT) || 3306
});

export const db = pool.promise();