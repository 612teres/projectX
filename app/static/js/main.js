document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications
    initializeNotifications();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize progress bars
    initializeProgressBars();
    
    // Initialize dropdowns
    initializeDropdowns();
});

function initializeDropdowns() {
    const notificationsButton = document.getElementById('notifications-menu-button');
    const notificationsDropdown = document.getElementById('notifications-dropdown');
    const userButton = document.getElementById('user-menu-button');
    const userDropdown = document.getElementById('user-dropdown');
    
    // Toggle notifications dropdown
    if (notificationsButton && notificationsDropdown) {
        notificationsButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = notificationsButton.getAttribute('aria-expanded') === 'true';
            
            // Close user dropdown if open
            if (userDropdown && userButton) {
                userDropdown.classList.add('hidden');
                userButton.setAttribute('aria-expanded', 'false');
            }
            
            // Toggle notifications
            notificationsButton.setAttribute('aria-expanded', !isExpanded);
            notificationsDropdown.classList.toggle('hidden');
            
            // Update notifications when opening dropdown
            if (!isExpanded) {
                updateNotificationsList();
            }
        });
    }
    
    // Toggle user dropdown
    if (userButton && userDropdown) {
        userButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = userButton.getAttribute('aria-expanded') === 'true';
            
            // Close notifications dropdown if open
            if (notificationsDropdown && notificationsButton) {
                notificationsDropdown.classList.add('hidden');
                notificationsButton.setAttribute('aria-expanded', 'false');
            }
            
            // Toggle user dropdown
            userButton.setAttribute('aria-expanded', !isExpanded);
            userDropdown.classList.toggle('hidden');
        });
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', (event) => {
        if (notificationsDropdown && !notificationsButton?.contains(event.target) && !notificationsDropdown.contains(event.target)) {
            notificationsDropdown.classList.add('hidden');
            notificationsButton.setAttribute('aria-expanded', 'false');
        }
        if (userDropdown && !userButton?.contains(event.target) && !userDropdown.contains(event.target)) {
            userDropdown.classList.add('hidden');
            userButton.setAttribute('aria-expanded', 'false');
        }
    });
}

function initializeNotifications() {
    // Initial notifications load
    updateNotificationBadge();
    updateNotificationsList();
    
    // Initialize WebSocket connection if user is authenticated
    const isAuthenticated = document.body.dataset.authenticated === 'true';
    if (isAuthenticated) {
        initializeWebSocket();
    }
    
    // Setup mark all as read button
    const markAllReadButton = document.getElementById('mark-all-read');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', () => {
            fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateNotificationBadge();
                    updateNotificationsList();
                }
            })
            .catch(error => console.error('Error marking all notifications as read:', error));
        });
    }
}

function initializeWebSocket() {
    let socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to WebSocket');
    });
    
    socket.on('notification', (data) => {
        updateNotificationBadge();
        updateNotificationsList();
        flashNotificationIcon();
    });
}

function initializeTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function(e) {
            const tooltipText = this.dataset.tooltip;
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg';
            tooltipEl.textContent = tooltipText;
            tooltipEl.style.top = `${e.pageY + 10}px`;
            tooltipEl.style.left = `${e.pageX + 10}px`;
            document.body.appendChild(tooltipEl);
            
            this.addEventListener('mouseleave', () => tooltipEl.remove(), { once: true });
        });
    });
}

function initializeProgressBars() {
    document.querySelectorAll('.progress-bar').forEach(bar => {
        const progress = parseFloat(bar.style.width);
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = `${progress}%`;
        }, 100);
    });
}

// Handle task status updates
const taskStatusSelects = document.querySelectorAll('.task-status-select');
taskStatusSelects.forEach(select => {
    select.addEventListener('change', function() {
        const taskId = this.getAttribute('data-task-id');
        const newStatus = this.value;
        updateTaskStatus(taskId, newStatus);
    });
});

// Function to show notifications
function showNotification(notification) {
    const notificationContainer = document.createElement('div');
    notificationContainer.className = 'fixed top-4 right-4 z-50 max-w-sm notification';
    
    // Set background color based on notification type
    let bgColor, icon;
    switch (notification.type) {
        case 'project':
            bgColor = 'bg-blue-500';
            icon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>`;
            break;
        case 'task':
            bgColor = 'bg-green-500';
            icon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>`;
            break;
        case 'deadline':
            bgColor = 'bg-red-500';
            icon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>`;
            break;
        default:
            bgColor = 'bg-gray-500';
            icon = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>`;
    }
    
    notificationContainer.innerHTML = `
        <div class="rounded-lg shadow-lg ${bgColor} text-white p-4 flex items-start space-x-4">
            <div class="flex-shrink-0">
                ${icon}
            </div>
            <div class="flex-1">
                <p class="text-sm font-medium">${notification.message}</p>
                <p class="mt-1 text-xs opacity-75">Just now</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="flex-shrink-0 ml-4 text-white hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notificationContainer);
    
    // Remove notification after 5 seconds
    setTimeout(() => {
        notificationContainer.remove();
    }, 5000);
}

// Task status update function
function updateTaskStatus(taskId, newStatus) {
    fetch(`/task/${taskId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Show success notification
            showNotification({
                type: 'task',
                message: data.message
            });
            
            // Update the task card status
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskCard) {
                const statusBadge = taskCard.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.textContent = data.task_status;
                    // Update status badge color
                    statusBadge.className = `status-badge px-2 py-1 text-xs font-medium rounded-full ${getStatusClass(data.task_status)}`;
                }
            }
        }
    })
    .catch(error => {
        console.error('Error updating task status:', error);
        showNotification({
            type: 'error',
            message: 'Failed to update task status. Please try again.'
        });
    });
}

// Helper function to get status badge classes
function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'todo':
            return 'bg-gray-100 text-gray-800';
        case 'in progress':
            return 'bg-blue-100 text-blue-800';
        case 'review':
            return 'bg-yellow-100 text-yellow-800';
        case 'completed':
            return 'bg-green-100 text-green-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

function updateNotificationBadge() {
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.textContent = data.count;
                badge.classList.toggle('hidden', data.count === 0);
            }
        })
        .catch(error => console.error('Error updating notification badge:', error));
}

function updateNotificationsList() {
    const container = document.getElementById('notifications-list');
    if (!container) return;

    fetch('/api/notifications')
        .then(response => response.json())
        .then(notifications => {
            if (notifications.length === 0) {
                container.innerHTML = '<div class="py-3 px-4 text-sm text-gray-500">No notifications</div>';
                return;
            }

            container.innerHTML = notifications.map(notification => `
                <div class="notification-item border-b border-gray-100 last:border-b-0">
                    <div class="p-4 hover:bg-gray-50 flex items-start space-x-4 ${notification.read ? 'opacity-75' : 'bg-blue-50'}" data-id="${notification.id}">
                        <div class="flex-shrink-0">
                            ${getNotificationIcon(notification.type)}
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm text-gray-900">${notification.message}</p>
                            <p class="text-xs text-gray-500 mt-1">
                                ${formatTimestamp(notification.timestamp)}
                            </p>
                        </div>
                        ${!notification.read ? `
                            <button onclick="markNotificationRead(${notification.id})" 
                                    class="flex-shrink-0 p-1 rounded-full text-gray-400 hover:text-gray-500 focus:outline-none">
                                <span class="sr-only">Mark as read</span>
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                          d="M5 13l4 4L19 7" />
                                </svg>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error updating notifications list:', error);
            container.innerHTML = '<div class="py-3 px-4 text-sm text-red-500">Error loading notifications</div>';
        });
}

function getNotificationIcon(type) {
    switch (type) {
        case 'project':
            return `<svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>`;
        case 'task':
            return `<svg class="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>`;
        case 'deadline':
            return `<svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>`;
        default:
            return `<svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>`;
    }
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // difference in seconds

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`;
    return date.toLocaleDateString();
}

function flashNotificationIcon() {
    const icon = document.getElementById('notifications-menu-button');
    if (icon) {
        icon.classList.add('animate-pulse');
        setTimeout(() => {
            icon.classList.remove('animate-pulse');
        }, 2000);
    }
}

function markNotificationRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateNotificationBadge();
            updateNotificationsList();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

// Initialize notifications when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Update notifications badge and list
    updateNotificationBadge();
    updateNotificationsList();
    
    // Connect socket when user is authenticated
    const isAuthenticated = document.body.dataset.authenticated === 'true';
    if (isAuthenticated) {
        socket.connect();
    }

    // Setup mark all as read button
    const markAllReadButton = document.getElementById('mark-all-read');
    if (markAllReadButton) {
        markAllReadButton.addEventListener('click', () => {
            fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    updateNotificationBadge();
                    updateNotificationsList();
                }
            })
            .catch(error => console.error('Error marking all notifications as read:', error));
        });
    }

    // Setup notification dropdown auto-update
    const notificationsButton = document.getElementById('notifications-menu-button');
    if (notificationsButton) {
        notificationsButton.addEventListener('click', () => {
            updateNotificationsList();
        });
    }
}); 