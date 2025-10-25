import {PriorityQueue} from '@datastructures-js/priority-queue';

export function getRandomInteger(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export class Patient {
    constructor(id, triageLevel, timeIn) {
        this.id = id;
        this.triageLevel = triageLevel;
        this.timeIn = timeIn.getTime();
        this.removed = false;
    }
}

export const comparePatients = (a,b) => {
    if (a.triageLevel !== b.triageLevel) 
        return a.triageLevel - b.triageLevel;
    return a.timeIn - b.timeIn;
}


export class ERQueue {
    constructor() {
        this.queue = new PriorityQueue(comparePatients);
        this.patientMap = new Map();
    }

    addPatient(patient) {
        this.queue.push(patient);
        this.patientMap.set(patient.id, patient);
    }

    removePatient(id) {
        const patient = this.patientMap.get(id);
        if (patient) {
            patient.removed = true;
            this.patientMap.delete(id);
        }
    }

    popNextPatient(copyQueue = null) {
        const queueToUse = copyQueue || this.queue;

        while (!queueToUse.isEmpty()) {
            const next = queueToUse.pop();
            if (!next.removed) {
                if (!copyQueue) this.patientMap.delete(next.id);
                return next;
            }
        }
        return null;
    }

    getCopyQueue() {
        const copy = new PriorityQueue(comparePatients);
        this.queue.toArray().forEach(p => copy.push(p));
        return copy;
    }

    getAllPatientsSorted() {
        const copy = this.getCopyQueue();
        const list = [];
        let patient;
        while ((patient = this.popNextPatient(copy)) !== null) {
            list.push(patient);
        }
        return list;
    }

    changePatientInfo(id, triageChange=null) {
        if (triageChange) {
            this.patientMap.get(id).triageLevel = triageChange;
        }
    }
}