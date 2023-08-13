/**
* Welcome to Cloudflare Workers! This is your first worker.
*
* - Run `npm run dev` in your terminal to start a development server
* - Open a browser tab at http://localhost:8787/ to see your worker in action
* - Run `npm run deploy` to publish your worker
*
* Learn more at https://developers.cloudflare.com/workers/
*/
import { Configuration, OpenAIApi } from "openai";
import fetchAdapter from "@haverstack/axios-fetch-adapter";

export interface Env {
    // Example binding to KV. Learn more at https://developers.cloudflare.com/workers/runtime-apis/kv/
    // MY_KV_NAMESPACE: KVNamespace;
    //
    // Example binding to Durable Object. Learn more at https://developers.cloudflare.com/workers/runtime-apis/durable-objects/
    // MY_DURABLE_OBJECT: DurableObjectNamespace;
    //
    // Example binding to R2. Learn more at https://developers.cloudflare.com/workers/runtime-apis/r2/
    // MY_BUCKET: R2Bucket;
    //
    // Example binding to a Service. Learn more at https://developers.cloudflare.com/workers/runtime-apis/service-bindings/
    // MY_SERVICE: Fetcher;
    //
    // Example binding to a Queue. Learn more at https://developers.cloudflare.com/queues/javascript-apis/
    // MY_QUEUE: Queue;
}

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        env.LOGGER.fetch('https://logger.spotyie.workers.dev', {
            method: 'POST',
            body: "woof"
        });
        request.arrayBuffer().then(buf => {
            fetch('https://logger.spotyie.workers.dev', {
                method: 'POST',
                body: "audiofile promise ressed"
            });
        });
        // const configuration = new Configuration({
        //     apiKey: env.OPENAI_API_KEY,
        //     baseOptions: {
        //         adapter: fetchAdapter
        //     }
        // });
        // const openai = new OpenAIApi(configuration);
        // try {
        //     const chatCompletion = await openai.createChatCompletion({
        //         model: "gpt-3.5-turbo-0613",
        //         messages: [{role: "user", content: "What's happening in the NBA today?"}],
        //         functions: [ ]
        //     });

        //     const msg = chatCompletion.data.choices[0].message!;
        //     console.log(msg.function_call)

        //     return new Response('Hello World!');
        // } catch (e: any) {
        //     return new Response(e);
        // }
        return new Response('Hello World!');
    },
};
