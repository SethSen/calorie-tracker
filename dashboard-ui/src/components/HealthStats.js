import React, { useEffect, useState } from 'react';
import '../App.css';

export default function HealthStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null);

    const getStats = () => {
        fetch('http://calorie-tracker.eastus2.cloudapp.azure.com/health/health_check')
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received Stats");
                    setStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
    };

    useEffect(() => {
        getStats(); // Initial fetch
        const interval = setInterval(() => getStats(), 5000); // Update every 5 seconds
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className="error">Error: {error.message}</div>;
    } else if (!isLoaded) {
        return <div>Loading...</div>;
    } else {
        const timestampString = stats['last_updated'];
        const savedTimestamp = new Date(timestampString);
        const currentTime = new Date();
        const timeDifferenceMs = currentTime - savedTimestamp;
        const secondsDifference = Math.floor(timeDifferenceMs / 1000);
        const minutesDifference = Math.floor(secondsDifference / 60);
        return (
            <div>
                <h1>Latest Health Stats</h1>
                <table className="StatsTable">
                    <tbody>
                        <tr>
                            <td>Receiver:</td>
                            <td>{stats['receiver_health']}</td>
                        </tr>
                        <tr>
                            <td>Storage:</td>
                            <td>{stats['storage_health']}</td>
                        </tr>
                        <tr>
                            <td>Processing:</td>
                            <td>{stats['processing_health']}</td>
                        </tr>
                        <tr>
                            <td>Audit:</td>
                            <td>{stats['audit_health']}</td>
                        </tr>
                    </tbody>
                </table>
                <h3>Last Updated: {minutesDifference} minutes ago</h3>
            </div>
        );
    }
}
