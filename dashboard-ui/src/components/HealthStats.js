import React, { useEffect, useState } from 'react'
import '../App.css';

export default function HealthStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {

        fetch(`http://calorie-tracker.eastus2.cloudapp.azure.com:8120/health_check`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        const timestampString = stats['last_updated'];
        const savedTimestamp = new Date(timestampString);
        const currentTime = new Date();
        const timeDifferenceMs = currentTime - savedTimestamp;
        const secondsDifference = Math.floor(timeDifferenceMs / 1000);
        const minutesDifference = Math.floor(secondsDifference / 60);
        return(
            <div>
                <h1>Latest Health Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<td colspan="2">Receiver: {stats['receiver_health']}</td>
						</tr>
						<tr>
							<td colspan="2">Storage: {stats['storage_health']}</td>
						</tr>
						<tr>
							<td colspan="2">Processing: {stats['processing_health']}</td>
						</tr>
                        <tr>
                            <td colspan="2">Audit: {stats['audit_health']}</td>
                        </tr>
					</tbody>
                </table>
                <h3>Last Updated: {minutesDifference} Ago</h3>

            </div>
        )
    }
}