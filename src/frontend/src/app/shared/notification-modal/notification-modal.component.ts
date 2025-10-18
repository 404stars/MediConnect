import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NotificationService, Notification } from '../../services/notification.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-notification-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="notification.show" class="modal-overlay" (click)="close()">
      <div class="notification-modal" 
           [ngClass]="'notification-' + notification.type"
           (click)="$event.stopPropagation()">
        <div class="notification-header">
          <i [class]="getIcon()" class="notification-icon"></i>
          <h3>{{ notification.title }}</h3>
          <button class="btn-close-modal" (click)="close()">×</button>
        </div>
        <div class="notification-body">
          <p>{{ notification.message }}</p>
        </div>
        <div class="notification-footer">
          <button class="btn btn-primary" (click)="close()">
            Entendido
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
      animation: fadeIn 0.2s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .notification-modal {
      background: white;
      border-radius: 16px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      max-width: 500px;
      width: 90%;
      animation: slideIn 0.3s ease-out;
      overflow: hidden;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-30px) scale(0.95);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .notification-header {
      padding: 2rem 2rem 1rem 2rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      position: relative;
      border-bottom: 1px solid #e9ecef;
    }

    .notification-icon {
      font-size: 2.5rem;
      flex-shrink: 0;
    }

    .notification-header h3 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
      color: #333;
      flex-grow: 1;
    }

    .btn-close-modal {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: transparent;
      border: none;
      font-size: 2rem;
      color: #666;
      cursor: pointer;
      padding: 0;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: all 0.2s ease;
    }

    .btn-close-modal:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: #333;
    }

    .notification-body {
      padding: 1.5rem 2rem;
    }

    .notification-body p {
      margin: 0;
      font-size: 1.1rem;
      line-height: 1.6;
      color: #555;
    }

    .notification-footer {
      padding: 1rem 2rem 2rem 2rem;
      display: flex;
      justify-content: flex-end;
    }

    .btn {
      padding: 0.75rem 2rem;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-primary {
      background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(74, 144, 226, 0.4);
    }

    /* Estilos según el tipo */
    .notification-warning .notification-icon {
      color: #ffc107;
    }

    .notification-error .notification-icon {
      color: #dc3545;
    }

    .notification-success .notification-icon {
      color: #28a745;
    }

    .notification-info .notification-icon {
      color: #17a2b8;
    }

    @media (max-width: 576px) {
      .notification-modal {
        width: 95%;
        margin: 1rem;
      }

      .notification-header {
        padding: 1.5rem 1.5rem 1rem 1.5rem;
      }

      .notification-header h3 {
        font-size: 1.25rem;
      }

      .notification-body {
        padding: 1rem 1.5rem;
      }

      .notification-body p {
        font-size: 1rem;
      }

      .notification-footer {
        padding: 1rem 1.5rem 1.5rem 1.5rem;
      }
    }
  `]
})
export class NotificationModalComponent implements OnInit, OnDestroy {
  notification: Notification = {
    type: 'info',
    title: '',
    message: '',
    show: false
  };

  private subscription?: Subscription;

  constructor(private notificationService: NotificationService) {}

  ngOnInit() {
    this.subscription = this.notificationService.notification$.subscribe(
      notification => {
        this.notification = notification;
      }
    );
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  close() {
    this.notificationService.hide();
  }

  getIcon(): string {
    switch (this.notification.type) {
      case 'warning': return 'bi bi-exclamation-triangle-fill';
      case 'error': return 'bi bi-x-circle-fill';
      case 'success': return 'bi bi-check-circle-fill';
      case 'info': return 'bi bi-info-circle-fill';
      default: return 'bi bi-info-circle-fill';
    }
  }
}
