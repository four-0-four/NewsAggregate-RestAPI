import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export interface EmailI {
    id?: number;
    address: string;
}

@Entity()
export class Email implements EmailI {
    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    address: string;
}