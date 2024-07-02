export default [
    {
        match: {
            predicate: { type: "uri", value: "https://w3.org/ns/bde/docker#status" }
        },
        callback: {
            url: "http://capture/.mu/delta", method: "POST"
        },
        options: {
            foldEffectiveChanges: true,
            resourceFormat: "v0.0.1",
            gracePeriod: 1000,
            ignoreFromSelf: false
        }
    },
    {
      match: {
            predicate: { type: "uri", value: "https://w3.org/ns/bde/docker#status" }
        },
        callback: {
            url: "http://stats/.mu/delta", method: "POST"
        },
        options: {
            foldEffectiveChanges: true,
            resourceFormat: "v0.0.1",
            gracePeriod: 1000,
            ignoreFromSelf: false
        }
    }
];
