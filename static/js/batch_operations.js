// Batch Operations JavaScript
let selectedUsers = new Set();
let currentSingleUser = null;

// Dropdown functionality
function toggleDropdown(event, button) {
    event.stopPropagation();
    const dropdown = button.closest('.dropdown');
    const isOpen = dropdown.classList.contains('show');
    
    // Close all dropdowns
    document.querySelectorAll('.dropdown.show').forEach(d => {
        d.classList.remove('show');
    });
    
    // Toggle current dropdown
    if (!isOpen) {
        dropdown.classList.add('show');
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.show').forEach(d => {
            d.classList.remove('show');
        });
    }
});

// Close modals when clicking outside
document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeAllModals();
        }
    });
});

function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.classList.remove('show');
    });
}

function updateBatchActions() {
    const batchActions = document.getElementById('batchActions');
    const batchCount = document.getElementById('batchCount');
    const count = selectedUsers.size;
    
    if (count > 0) {
        batchActions.classList.add('show');
        batchCount.textContent = `${count} selected`;
    } else {
        batchActions.classList.remove('show');
    }
}

function toggleUserSelection(checkbox, userId) {
    if (checkbox.checked) {
        selectedUsers.add(userId);
    } else {
        selectedUsers.delete(userId);
    }
    updateBatchActions();
}

function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.user-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = checkbox.checked;
        const userId = cb.dataset.userId;
        if (checkbox.checked) {
            selectedUsers.add(userId);
        } else {
            selectedUsers.delete(userId);
        }
    });
    updateBatchActions();
}

function clearSelection() {
    selectedUsers.clear();
    document.querySelectorAll('.user-checkbox').forEach(cb => cb.checked = false);
    const selectAll = document.getElementById('selectAll');
    if (selectAll) selectAll.checked = false;
    updateBatchActions();
}

function getCSRFToken() {
    // First try hidden input in any form on the page
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;

    // Fallback: read from cookie using regex
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

// ===== SINGLE USER MODALS =====

function openSingleDeleteModal(userId, username, email) {
    console.log('openSingleDeleteModal called', userId, username, email);
    currentSingleUser = { id: userId, username: username, email: email };
    document.getElementById('singleDeleteUserInfo').innerHTML = `
        <div class="user-info-row">
            <div class="user-info-avatar">${username.charAt(0).toUpperCase()}</div>
            <div>
                <div class="user-info-name">${username}</div>
                <div class="user-info-email">${email}</div>
            </div>
        </div>
    `;
    document.getElementById('singleDeleteUsernameInput').value = '';
    document.getElementById('singleDeleteSubmitBtn').disabled = true;
    document.getElementById('singleDeleteModal').classList.add('show');
}

function closeSingleDeleteModal() {
    document.getElementById('singleDeleteModal').classList.remove('show');
    currentSingleUser = null;
}

document.getElementById('singleDeleteUsernameInput')?.addEventListener('input', function() {
    const submitBtn = document.getElementById('singleDeleteSubmitBtn');
    submitBtn.disabled = this.value !== currentSingleUser?.username;
});

async function confirmSingleDelete() {
    if (!currentSingleUser) return;

    const btn = document.getElementById('singleDeleteSubmitBtn');
    btn.disabled = true;
    btn.textContent = 'Deleting...';

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `confirmation=${encodeURIComponent(currentSingleUser.username)}`
        });

        const data = await response.json();

        if (data.success) {
            closeSingleDeleteModal();
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            window.location.href = '/users/list/';
        } else {
            alert('Error: ' + data.message);
            btn.disabled = false;
            btn.textContent = 'Delete User';
        }
    } catch (error) {
        alert('Error: ' + error.message);
        btn.disabled = false;
        btn.textContent = 'Delete User';
    }
}

function openSingleDeactivateModal(userId, username, email, activeBorrows) {
    currentSingleUser = { id: userId, username: username, email: email };
    const borrowCount = parseInt(activeBorrows) || 0;
    const borrowHtml = borrowCount > 0
        ? `<div class="user-info-borrow-warning">
               <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;flex-shrink:0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
               <span>${borrowCount} active borrow${borrowCount !== 1 ? 's' : ''} — user won't be able to return books while deactivated</span>
           </div>`
        : '';
    document.getElementById('singleDeactivateUserInfo').innerHTML = `
        <div class="user-info-row">
            <div class="user-info-avatar">${username.charAt(0).toUpperCase()}</div>
            <div>
                <div class="user-info-name">${username}</div>
                <div class="user-info-email">${email}</div>
            </div>
        </div>
        ${borrowHtml}
    `;
    document.getElementById('singleDeactivateModal').classList.add('show');
}

function closeSingleDeactivateModal() {
    document.getElementById('singleDeactivateModal').classList.remove('show');
    currentSingleUser = null;
}

async function confirmSingleDeactivate() {
    if (!currentSingleUser) return;

    const btn = document.querySelector('#singleDeactivateModal .btn-warning');
    if (btn) { btn.disabled = true; btn.textContent = 'Deactivating...'; }

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/deactivate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        });

        const data = await response.json();

        if (data.success) {
            closeSingleDeactivateModal();
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            window.location.reload();
        } else {
            alert('Error: ' + data.message);
            if (btn) { btn.disabled = false; btn.textContent = 'Deactivate'; }
        }
    } catch (error) {
        alert('Error: ' + error.message);
        if (btn) { btn.disabled = false; btn.textContent = 'Deactivate'; }
    }
}

function openSingleActivateModal(userId, username, email) {
    currentSingleUser = { id: userId, username: username, email: email };
    document.getElementById('singleActivateUserInfo').innerHTML = `
        <div class="user-info-row">
            <div class="user-info-avatar">${username.charAt(0).toUpperCase()}</div>
            <div>
                <div class="user-info-name">${username}</div>
                <div class="user-info-email">${email}</div>
            </div>
        </div>
    `;
    document.getElementById('singleActivateModal').classList.add('show');
}

function closeSingleActivateModal() {
    document.getElementById('singleActivateModal').classList.remove('show');
    currentSingleUser = null;
}

async function confirmSingleActivate() {
    if (!currentSingleUser) return;

    const btn = document.querySelector('#singleActivateModal .btn-success');
    if (btn) { btn.disabled = true; btn.textContent = 'Activating...'; }

    try {
        const response = await fetch(`/users/${currentSingleUser.id}/activate/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        });

        const data = await response.json();

        if (data.success) {
            closeSingleActivateModal();
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            window.location.reload();
        } else {
            alert('Error: ' + data.message);
            if (btn) { btn.disabled = false; btn.textContent = 'Activate'; }
        }
    } catch (error) {
        alert('Error: ' + error.message);
        if (btn) { btn.disabled = false; btn.textContent = 'Activate'; }
    }
}

// ===== BATCH OPERATIONS =====

function batchActivate() {
    if (selectedUsers.size === 0) return;
    
    // Open modal instead of confirm
    document.getElementById('batchActivateCount').textContent = selectedUsers.size;
    document.getElementById('batchActivateModal').classList.add('show');
}

function closeBatchActivateModal() {
    document.getElementById('batchActivateModal').classList.remove('show');
}

async function confirmBatchActivate() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        
        const response = await fetch('/users/batch/activate/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function batchDeactivate() {
    if (selectedUsers.size === 0) return;
    
    // Open modal instead of confirm
    document.getElementById('batchDeactivateCount').textContent = selectedUsers.size;
    document.getElementById('batchDeactivateModal').classList.add('show');
}

function closeBatchDeactivateModal() {
    document.getElementById('batchDeactivateModal').classList.remove('show');
}

async function confirmBatchDeactivate() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        
        const response = await fetch('/users/batch/deactivate/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function batchDelete() {
    if (selectedUsers.size === 0) return;
    
    // Open modal for batch delete
    document.getElementById('batchDeleteCount').textContent = selectedUsers.size;
    document.getElementById('batchDeleteInput').value = '';
    document.getElementById('batchDeleteSubmitBtn').disabled = true;
    document.getElementById('batchDeleteModal').classList.add('show');
}

function closeBatchDeleteModal() {
    document.getElementById('batchDeleteModal').classList.remove('show');
}

document.getElementById('batchDeleteInput')?.addEventListener('input', function() {
    const submitBtn = document.getElementById('batchDeleteSubmitBtn');
    submitBtn.disabled = this.value !== 'DELETE';
});

async function confirmBatchDelete() {
    if (selectedUsers.size === 0) return;
    
    try {
        const formData = new FormData();
        selectedUsers.forEach(id => formData.append('user_ids[]', id));
        formData.append('confirmation', 'DELETE');
        
        const response = await fetch('/users/batch/delete/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionStorage.setItem('pendingToast', JSON.stringify({ message: data.message, type: 'success' }));
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Show any pending toast stored before a page reload
document.addEventListener('DOMContentLoaded', function () {
    const pending = sessionStorage.getItem('pendingToast');
    if (pending) {
        sessionStorage.removeItem('pendingToast');
        try {
            const { message, type } = JSON.parse(pending);
            // showToast is defined in toast_notifications.html which loads before this script
            if (typeof showToast === 'function') {
                showToast(message, type);
            }
        } catch (e) {
            // ignore parse errors
        }
    }
});
