const WebSocket = require("ws")
const fs = require('fs')
const EulerToolsClient = require("./EulerToolsClient")

const EULERSCAN_ENDPOINT = "wss://escan-mainnet.euler.finance"

const eulerClient = new EulerToolsClient({
  version: "example script",
  endpoint: EULERSCAN_ENDPOINT,
  WebSocket,
  onConnect: () => console.log("Euler History Client connected"),
  onDisconnect: () => console.log("Euler History Client disconnected"),
})

const main = () => {
    eulerClient.connect()

    //let result
    const id = eulerClient.sub({
        cmd: "sub",
        query: {
            topic: "accounts",
            by: "healthScore",
            healthMax: 10000000000000000000,
            limit: 10000
        }
    },
        async (err, patch) => {
            if (err) throw new Error(err.message)

            eulerClient.unsubscribe(id) // don't unsubscribe if using immer      
            eulerClient.shutdown() // best to disconnect if just one time query    
            
            console.log(JSON.stringify(patch.result))

            console.log('Saving files')
            fs.writeFileSync("ethereum_euler.json", JSON.stringify(patch.result))
            console.log('Saved file')
        },
    )
}

main()