import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Notification {
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  show: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationSubject = new BehaviorSubject<Notification>({
    type: 'info',
    title: '',
    message: '',
    show: false
  });

  public notification$ = this.notificationSubject.asObservable();

  showWarning(title: string, message: string) {
    this.notificationSubject.next({
      type: 'warning',
      title,
      message,
      show: true
    });
  }

  showError(title: string, message: string) {
    this.notificationSubject.next({
      type: 'error',
      title,
      message,
      show: true
    });
  }

  showSuccess(title: string, message: string) {
    this.notificationSubject.next({
      type: 'success',
      title,
      message,
      show: true
    });
  }

  showInfo(title: string, message: string) {
    this.notificationSubject.next({
      type: 'info',
      title,
      message,
      show: true
    });
  }

  hide() {
    const currentNotification = this.notificationSubject.value;
    this.notificationSubject.next({
      ...currentNotification,
      show: false
    });
  }
}
