const CF_ZONE_ID = '404b821aad974edb640129f977823acd';
const CF_API_KEY = 'b48be2da12c2b38a21c3d5dabd6bcbdd23c30';
const CF_AUTH_EMAIL = 'aparna@prismax.ai';

export default {
    async fetch(request, env, ctx) {
        // Forward POST to origin
        const response = await fetch(request);
        
        // Only purge cache if POST was successful
        if (response.ok) {
            let purgeCacheError = false;
            try {
                // Purge the cache
                const purgeResponse = await fetch(
                    `https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Auth-Email': CF_AUTH_EMAIL, 
                            'X-Auth-Key': CF_API_KEY 
                        },
                        body: JSON.stringify({
                            prefixes: [
                                "beta-user.prismaxserver.com/get_blockchain_config_address", 
                                "user.prismaxserver.com/get_blockchain_config_address"
                            ]
                        })
                    }
                );
                const purgeRes = await purgeResponse.json();
                console.log('PURGE RESPONSE JSON');
                console.log(purgeRes);
    
                if (purgeRes.success) {
                    // Add header to indicate cache purge was triggered
                    const modifiedResponse = new Response(response.body, response);
                    modifiedResponse.headers.set('X-Cache-Purge-Triggered', 'true');
                    return modifiedResponse;
                } else {
                    purgeCacheError = true;
                    console.error(`Failed to purge cache: ${purgeRes?.errors}`);
                }
            } catch (error) {
                purgeCacheError = true;
            }

            if (purgeCacheError) {
                // Modify the response body to indicate the cache purge error
                const originalBody = await response.json();
                const modifiedBody = {
                    success: false,
                    msg: "Error resetting the Cloudflare cache. Manually clear the Cloudflare cache to avoid inconsistencies now. Live paused status has been updated in the database.",
                    robot_id: originalBody.robot_id,
                    live_paused: originalBody.live_paused
                };
                // Create new response with modified body
                const modifiedResponse = new Response(
                    JSON.stringify(modifiedBody),
                    {
                        status: 500,
                        headers: {
                            ...Object.fromEntries(response.headers),
                            'Content-Type': 'application/json',
                            'X-Cache-Purge-Error': 'true'
                        }
                    }
                );
                return modifiedResponse;
            }
        }

        return response;
    }
};