# Asyntai

**Author:** asyntai
**Version:** 0.0.1
**Type:** tool

## Description

Give your agent the knowledge of a whole website.

Point Asyntai at a domain. Asyntai crawls the site, reads the product feed, and keeps both fresh on its own. This plugin then lets any Dify agent or workflow ask that website a question and get the answer a visitor would get, built from the real pages and the real prices.

The same plugin opens the other side of the website: the chats visitors had, and the email addresses and phone numbers they left behind.

## What you can build

- **A support agent that knows a client's whole site.** No crawler, no chunking, no embedding job to maintain. One domain, one API key, and the agent answers.
- **An email answering workflow.** Read the incoming question, call *Ask the website*, write the reply with real product and policy detail.
- **A lead follow-up flow.** Read new leads, open the chat each visitor had, and write a reply that continues that conversation instead of starting over.
- **A knowledge pipeline.** Push release notes, policies or a price list into the knowledge base from any Dify workflow, and the website chat starts using them at once.

## Tools

| Tool | What it does |
| --- | --- |
| Ask the website | Answers a question from the website's pages, products and knowledge base. |
| Add a page to the knowledge base | Reads a URL and stores its content. |
| Add a note to the knowledge base | Stores a title and a text you write. |
| List leads | Returns visitors who left an email address or a phone number, newest first. |
| Read a chat | Returns every message of one website chat, in order. |
| List websites | Returns each website on the account with its ID and domain. |

## Setup

1. Create an account at [asyntai.com](https://asyntai.com) and add your website. Asyntai starts the crawl on its own.
2. Open **Settings**, then **API**, and copy the API key. The API is part of the Starter plan and above.
3. In Dify, open **Tools**, find **Asyntai**, and press **Authorize**.
4. Paste the API key. Dify checks it at once against your account.

## Usage

Add any of the six tools to an agent or a workflow node.

**One website.** Leave *Website ID* empty. Every tool then uses the primary website on the account.

**Several websites.** Run **List websites** once to get the IDs, then set *Website ID* on the tool. One Asyntai account holds many websites, so one Dify workspace can serve many clients.

**Conversation memory.** *Ask the website* takes a *Session ID*. Send the same value on every turn and Asyntai keeps the history of that conversation.

## For agencies

One Asyntai account carries several client websites at once, each with its own knowledge base and its own chat widget. Two ways to earn from it:

- **Resell.** The Pro plan holds up to 20 websites and removes the Asyntai badge, so the widget carries your brand and you bill the client.
- **Refer.** The affiliate programme pays 20% recurring, with a dashboard for clicks, signups and commission. Join at [asyntai.com/become-affiliate/](https://asyntai.com/become-affiliate/).

## Support

Write to [hello@asyntai.com](mailto:hello@asyntai.com).
