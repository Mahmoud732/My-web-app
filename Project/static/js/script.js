document.addEventListener('DOMContentLoaded', function () {
    fetchTimeUntilMidnight();
    setInterval(fetchTimeUntilMidnight, 1000); // Update every second

    function fetchTimeUntilMidnight() {
        fetch('/time_until_midnight')
            .then(response => response.json())
            .then(data => updateCounter(data.hours, data.minutes, data.seconds))
            .catch(error => console.error('Error fetching time until midnight:', error));
    }

    function updateCounter(hours, minutes, seconds) {
        const counter = document.getElementById('time-counter');
        counter.innerHTML = `${hours} hours, ${minutes} minutes, ${seconds} seconds`;
    }

    // Fetch user data function
    function fetchUsers() {
        fetch('/api/users')
            .then(response => response.json())
            .then(users => renderUsers(users))
            .catch(error => console.error('Error fetching users:', error));
    }

    // Initial fetch of users on page load
    fetchUsers();

    // Function to render users in the table
    function renderUsers(users) {
        const tableBody = document.querySelector('tbody');
        tableBody.innerHTML = ''; // Clear existing rows

        users.forEach(user => {
            const row = `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.password}</td>
                    <td>${user.start_date}</td>
                    <td>${user.end_date}</td>
                    <td>${user.remaining_days}</td>
                    <td>
                        <a href="/edit_user/${user.id}" class="button edit">Edit</a>
                        <form action="/delete_user/${user.id}" method="post" onsubmit="return confirm('Are you sure you want to delete this user?')">
                            <button type="submit" class="button delete">Delete</button>
                        </form>
                    </td>
                </tr>
            `;

            tableBody.innerHTML += row;
        });
    }

    // Event listener for refresh button
    const refreshButton = document.getElementById('refresh-button');
    refreshButton.addEventListener('click', function () {
        fetchUsers();
    });

    function formatDate(dateString) {
        const date = new Date(dateString);
        const day = date.getDate();
        const month = date.getMonth() + 1; // Month is zero-based
        const year = date.getFullYear();

        return `${day}/${month}/${year}`;
    }
});
