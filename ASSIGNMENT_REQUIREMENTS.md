Assignment 2: Interactive Visualization
Due: Sun, Nov 8 at 11:55pm
Submit your assignment →
Overview
An interactive visualization does more than put data on a screen: it hands the viewer a set of controls and lets them find the story themselves. In this assignment you act as both designer and developer, building a tool that makes exploring a dataset intuitive, engaging and revealing. The purpose is to get hands-on experience implementing interaction techniques — and, just as importantly, to think about which techniques actually suit the data you chose and the audience you have in mind.

We have seen in class how a single well-chosen interaction can turn a static table into a discovery tool: dynamic queries let the zipdecode and NameVoyager applications expose patterns in zip codes and baby names that no static chart shows, and treemaps, first invented to display hierarchical file systems, were later adapted into an interactive map of the stock market. Your job is to make that kind of choice for yourself.

What you will do: design and implement a web-based interactive visualization — in practice several smaller linked visualizations forming one dashboard — aimed at answering a compelling question about a dataset you choose. Doing some exploratory analysis first will help you work out which subset of the data and which interactions are the most promising. You are not obliged to convey everything about the data: focus on a compelling subset.

The design questions to keep asking yourself: What story or insight does this dataset hold? How can a user interact with the visualization to uncover that story? Which techniques best support exploration and understanding? Which aspects of the dataset are the most compelling? Which visual encodings and interaction techniques suit this data and this audience?

Dataset policy: you may use any dataset you like. Public open data, an API you crawl yourself, data from your own research, or the OpenAlex table you built in Assignment 1 — all are acceptable, as long as it is rich enough to support several linked views and you can document where it came from. Some starting points are listed under Getting Started.

Individual work policy: this is an individual assignment. You may discuss ideas with classmates, ask questions in class, and use AI assistance, but the design decisions, the code and the write-up must be your own.

Two requirements make this assignment different from a gallery of charts. First, cross-view interaction is mandatory: your dashboard needs at least three views and at least two cross-view brushing pairs, so that selecting in one view immediately changes what another view shows. Second, the views must be connected by a defensible data exploration logic — a reason why a viewer moves from this view to that one — and you will be asked to argue for that logic in your write-up.

Getting Started
Before you begin, make sure you have the following:

A dataset of your own choosing, with at least one categorical attribute, one quantitative attribute, and ideally a temporal or spatial one, so that several distinct views are possible
Lab Tutorials 3 and 4 completed — they cover the interaction and transition techniques this assignment is built on
JavaScript basics: fetch, promises, array methods, and the DOM
Enough Python or Node to write a handful of HTTP endpoints
Git and GitHub, from Assignment 0
Screen-recording software with microphone input, for the demo video
Useful links for this assignment:

Chicago Crimes, 2001 to present (City of Chicago open data)
NOAA Daily Global Historical Climatology Network (daily U.S. weather)
Opportunity Insights: social mobility data (Raj Chetty group, Harvard)
data.gov — U.S. federal open data catalog
Lab Tutorial 3: D3.js Interactions
Lab Tutorial 4: D3.js Animation
Setting Up Your Environment
Step 1: Choose your dataset and write down the question

Settle on the dataset and on the one compelling question you want it to answer before you write any code. Everything downstream — which views you build, how they are linked, what your video says — follows from that question. Then check that the dataset can carry a multi-view dashboard: enough rows to be interesting, a category to filter on, a quantity to compare, and a third dimension that can anchor a view of its own.

The three datasets linked above are known to work well for this kind of tool, but you are free to use anything else: a city open-data portal, a public API in a domain you care about, GBIF, the World Bank, Kaggle, or your own research data.

If you use a source that publishes several related tables, joining two of them often produces a much richer exploratory process than either alone.

Reusing your Assignment 1 OpenAlex table is allowed and saves you the collection time, but the design work has to be new.

Sanity-check the data early: value ranges, missing values, duplicate rows. Finding out on the last day that a column is mostly empty is an expensive discovery.

Step 2: Sketch the dashboard before you build it

On paper, draw the layout: which views, where, encoding what — and then the part people skip, what happens to every other view when the user selects something in one of them. Photograph the sketch; it belongs in your write-up as evidence of the design process.

For each view write one sentence: "this view answers ___". If you cannot finish the sentence, the view does not belong in the dashboard.

Draw the coordination explicitly: an arrow from the view being brushed to every view that reacts, labelled with what the reaction is — filter, highlight, or re-aggregate.

Step 3: Build the backend

Unlike a purely static visualization, this assignment requires server-side support: a small backend that owns the data and answers requests from the browser. Python with FastAPI or Flask is the shortest path if you are coming from Assignment 1; Node with Express is equally acceptable. Load the dataset once at startup and expose a few JSON endpoints — the slice the dashboard needs, plus whatever filtered or aggregated queries your interactions require.

conda activate dvjupyter && pip install fastapi uvicorn pandas — Python backend, reusing the environment from Assignment 1
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

df = pd.read_csv("data/records.csv")

@app.get("/api/records")
def records(category: str | None = None, year_min: int | None = None):
    out = df
    if category:
        out = out[out["category"] == category]
    if year_min:
        out = out[out["year"] >= year_min]
    return out.to_dict(orient="records")
— A minimal filtered endpoint — run it with: uvicorn main:app --reload --port 8000
Without the CORS middleware the browser blocks every request from your frontend, and the console shows a CORS error rather than a 404.

Load and clean the data once at import time. Re-reading the CSV inside the request handler makes every interaction feel sluggish.

FastAPI serves interactive API docs at /docs, which is the fastest way to test an endpoint before you wire it to a chart.

Step 4: Build the frontend

Build the client with whatever you are most productive in — a plain HTML page with D3, or a React app as in Lab Tutorial 1. Fetch from your backend, keep the current selection in a single place, and re-render the dependent views from that shared state. Serve the page over HTTP; opening the file directly with file:// breaks both fetch and module imports.

npx create-react-app dashboard --template typescript && cd dashboard && npm install d3 @types/d3 && npm start — React frontend on http://localhost:3000, talking to the API on port 8000
python3 -m http.server 5173 — Or, for a plain HTML + D3 frontend: serve the folder at http://localhost:5173
One source of truth for the selection. Every view reads it and no view keeps a private copy — this is what stops the coordination drifting out of sync.

Keep the API base URL in a single constant so switching from localhost to a deployed backend is a one-line change.

Step 5: Publish the site (or run it cleanly on localhost)

Deploying the project publicly is the ideal outcome, and the frontend half is easy to host on GitHub Pages. Create a new public repository, clone it, and copy your frontend into it, keeping index.html at the top level of the folder. Push the code, then open Settings, choose Pages, and set the source branch (e.g. main). Your site appears at [github-username].github.io/[repo-name] — GitHub says this takes up to ten minutes, though in practice it can be longer. Once it is live, the Pages tab shows a confirmation with the URL.

CIS4930-A2/
├── index.html
├── css/
│   └── styles.css
└── js/
    └── script.js
— index.html must sit at the top level of the repository for GitHub Pages to serve it. The data stays on your backend; the frontend fetches it from the API.
git init && git add . && git commit -m "first commit" && git branch -M main
git remote add origin https://github.com/<your-username>/CIS4930-A2.git
git push -u origin main
— Push an existing local project to a new GitHub repository
GitHub Pages serves static files only, so it can host your frontend but not your backend. For the backend, free tiers on Render, Railway, Fly.io or PythonAnywhere will run a small Python or Node service; remember to allow your frontend origin in the backend CORS settings and to point the frontend at the deployed API URL.

If deploying the backend turns out to be more than you want to take on, a project that runs entirely on localhost is fully acceptable. In that case your README and your demo video are what show the grader a working system, so both need to be good.

Try a deployment early — at least a couple of days before the deadline — rather than discovering hosting problems on the last night.

You can start with a private repository and switch it to public once you are ready to share it.

If the data fails to load on the deployed site but works locally, check your file paths and the API base URL first; those two account for nearly every case.

Step 6: Record the demo video

Record your screen with narration using QuickTime, OBS, Zoom or the free tier of Loom. The video serves two purposes: it timestamps your project so the graded version is fixed at the deadline, and — because your write-up cannot show interaction — it is where you demonstrate the tool actually working. Walk through the background of your analysis, what you set out to learn, how you explored the data with your own dashboard, and the story you arrived at.

Rehearse once. An unrehearsed screen recording spends its first two minutes looking for the right browser tab.

Narrate what you are learning, not what you are clicking. "Selecting this district drops the trend in every other view" is worth far more than "now I click here".

Record at a window size where your axis labels are legible in the exported file, and check the export rather than the preview.

Other ways to serve the site locally: flask run --port 8000 for a Flask backend; node server.js or npx express-generator for a Node backend; npm start for a React frontend, python3 -m http.server for a plain HTML frontend; GitHub Pages for the deployed frontend, with Render, Railway, Fly.io or PythonAnywhere for the deployed backend.

Debugging Tips
A blank chart with no console error is almost always an empty data array. Log the response before you touch the D3 code.
"Blocked by CORS policy" is a backend problem, not a frontend one: enable CORS on the server rather than working around it in the browser.
If a brush selects but nothing else updates, check that the other views re-read the shared state. The usual bug is a view rendered once on load and never again.
Re-fetching from the server on every mousemove makes brushing feel broken. Filter on the client for continuous interactions and reserve server round-trips for coarse changes such as switching a category or a year range.
Give every view an explicit empty state. A selection that matches no records should say so, not render an axis with nothing under it.
Keep object identity stable in your D3 data joins by passing a key function, or transitions between filtered states will animate the wrong marks.
On the deployed site, a chart that works locally and breaks in production is usually a relative path or a hard-coded localhost URL.
Deliverables
Submitting
Submit via Dropbox file request (link on this page) by Sun, Nov 8 at 11:55pm. Accepted file types: zip, mp4, txt, pdf.

Upload four things to the Dropbox file request:


Your project source as a ZIP named LastName_FirstName_A2.zip, containing the frontend, the backend, the dataset (or the script that fetches it), and a README with the exact commands to run both halves.

Your narrated demo video as an MP4 named LastName_FirstName_A2_demo.mp4 — or, if you host it elsewhere, put an unlisted video link in LastName_FirstName_A2_links.txt instead.

A text file named LastName_FirstName_A2_links.txt with the URL of your deployed site. If the project runs only on localhost, say so on that line and point to the start-up commands in your README.

Your write-up as a PDF report named LastName_FirstName_A2_report.pdf.
Upload your report here: https://www.dropbox.com/request/rda6dyejueb17ww02cuf

Formatting
The ZIP must contain a README with the exact commands to install dependencies and start both the backend and the frontend, including the ports. A grader who cannot start your project cannot grade it — test the README yourself in a fresh clone.
Keep the frontend and backend in separate top-level folders, and leave node_modules and virtual environments out of the ZIP.
Include the dataset if it is small enough; otherwise include the download script plus a sample file and say so in the README.
The web URL and the video both matter for grading, so make sure you have submitted all four items.
Never submit an API key or any other credential. Read secrets from environment variables and list the required variable names in the README.
This is individual work. Any AI assistance must be disclosed in the write-up; undisclosed use is an academic integrity issue, while disclosed use costs you nothing.
Writeup
Your report should be a PDF of about 600 to 1200 words, and should include the following sections:

Introduction to your dataset: What the data is, where it came from, and the background a reader needs. State the variables or the subset you chose to focus on, and the question your dashboard is built to answer.
Rationale for your design decisions: List the interactions you implemented. Explain how you chose your particular visual encodings and interaction techniques, which alternatives you considered, and how you arrived at your final choices.
Exploration logic across views: The argument that your views form a coherent whole rather than a set of separate charts: the intended path through the dashboard, and what a viewer learns at each step that the previous view could not tell them. Document both coordination pairs here, naming the source view, the dependent view, and what happens to the dependent view when the interaction fires.
System architecture: How the frontend and backend are split, the endpoints you exposed, what the server computes versus what the client computes, and why you drew the line there. Say whether the site is deployed or runs on localhost.
References to data resources: List the data source you used. If your work adapts or builds on an existing visualization example, cite that as well.
Overview of your development process: Roughly how many hours you spent building the application, which aspects took the most time, and what went wrong along the way.
Summary of AI usage (optional): If you used AI tools such as ChatGPT, Cursor or Copilot, briefly describe what you used them for and what you changed about what they produced. Required if you used any.
Extra Credit Features (optional): Only if you are claiming extra credit: a clearly labelled section describing each feature, why it is advanced or innovative, and how it goes beyond the requirements.
Scoring
Total points: 25

A list of interactive visualizations (at least three views) (7 points): Excellent: three or more distinct, well-encoded views, each carrying its own question, with titles, labelled axes, legends and captions, plus in-view interaction such as zooming, tooltips or highlighting. Good: three views that work but lack polish, with minor design flaws or unclear elements. Poor: fewer than three views, or encodings that hinder rather than help understanding.
Visualization coordination (at least two cross-view brushing pairs) (8 points): Excellent: at least two distinct coordinated view pairs, where brushing or selecting in one view immediately and correctly updates the other; selection state is visible, reversible and smooth. Good: coordination works but is limited to a single pair, or one dependent view responds incompletely. Poor: no working cross-view interaction, or views that only look linked.
Full-stack website completeness (4 points): Excellent: a working frontend and backend, data served over your own API, no noticeable bugs, and a README a grader can follow on a clean machine. Good: mostly functional with minor issues. Poor: significant bugs, a missing half of the stack, or a project the grader cannot start.
Write-up (PDF report) (3 points): Excellent: covers the dataset, the design rationale, the exploration logic, the architecture, the data references and the development process, with honest reflection and AI disclosure. Good: adequate but with gaps or superficial reflection. Poor: incomplete or unclear, missing sections or references.
Demo video (3 points): Excellent: a short, functional narrated recording that shows every implemented feature and walks through the analysis background, the purpose, the exploration process and the resulting story. Good: demonstrates most key features, with minor gaps or unclear moments. Poor: incomplete or unclear, or fails to show the core functionality.
Extra credit (up to 3 bonus points):

Declared extra credit features (+3 points): Extra credit is for work that meaningfully goes beyond the required elements. It is not automatic and is evaluated conservatively, on quality and intent rather than quantity. To be considered, include a clearly labelled "Extra Credit Features" section in your write-up explaining what the feature is, why it is advanced or innovative, and how it goes beyond the requirements. Undocumented features receive nothing; features that are declared but not approved are simply graded as part of the base assignment, with no penalty. Examples: a map with linked brushing, a temporal animation driven by a play control, semantic zoom, a comparison mode holding two selections side by side, or real server-side computation such as aggregation over a dataset too large to send to the browser.
Checklist

Choose a dataset and write down the compelling question you want to answer with it.

Build at least three distinct interactive views, each with a title, labelled axes, a legend where needed and a caption.

Implement at least two cross-view brushing pairs, so that selecting in one view immediately updates another.

Build both halves of the system: a backend that serves the data, and a frontend that renders the dashboard.

Write the PDF report, with references, and export it as LastName_FirstName_A2_report.pdf.

Deploy your visualization as a public webpage, or confirm it starts cleanly from a fresh clone on localhost.

Record a short narrated demo video.

Upload all four items — the project ZIP, the demo video, the links file and the PDF report — to the Dropbox file request before the deadline.
Assignment Requirements
Required Element 1: A List of Interactive Visualizations (7 points)
Build at least three views. The goal is not an overwhelming dashboard but a focused, elegant and intuitive design in which each view is a competent visualization on its own and carries a question of its own.

At least three distinct views (required). They should differ in what they show, not merely in colour — for example a distribution, a trend over time, and a detail or ranking view. Reusing a chart type is acceptable only when the two views answer clearly different questions.
Encode the data properly. Every view needs a title, labelled axes with units, a legend wherever colour or size carries meaning, and a caption saying what it shows. Keep one shared colour scale across the dashboard: a category must not be blue in one view and orange in another.
Give each view its own in-view interaction from the exploration category: panning and/or zooming, details-on-demand such as tooltips, highlighting, annotation, or another narrative feature that draws attention to items of interest and provides additional context.
Lay the dashboard out deliberately. The view a reader should see first belongs where the eye lands first, and views that are linked should be close enough for a viewer to see them change together.
Give the dashboard an exploration logic and be able to defend it. Write down the intended path — for example overview, then filtered subgroup, then individual record — and make sure the layout supports that path. This argument goes in your write-up, and it is what separates a dashboard from a collection of charts.
We expect most students will use D3.js, but you are free to use other web-based libraries such as Vega-Lite, Plotly or Observable Plot. Unlike a static visualization exercise, this assignment requires server-side support: the data must arrive from your own backend rather than from a file bundled into the page.
Focus on a compelling subset rather than everything the dataset contains. A polished, simple tool beats a sprawling, incomplete one.
Hints:

Overview first, zoom and filter, then details on demand is a reliable default structure. Deviating from it is fine, but then say what you replaced it with.
Three views done well beat six done carelessly. The credit here is for quality per view, not chart count.
Aggregate before you plot. A scatterplot of 200,000 points is a grey rectangle; binning, sampling or aggregating is a design decision worth describing.
Position tooltips relative to the pointer and flip them near the window edge, or half of yours will be cut off at the right of the screen.
Show a draft to a classmate and watch them use it without explaining anything first. Where they hesitate is where your design needs work.
Required Element 2: Visualization Coordination (8 points)
The heart of the assignment. Your dashboard must support at least two cross-view brushing pairs: two distinct coordination relationships in which selecting or brushing in one view immediately changes what another view shows.

At least two coordinated view pairs (required). One pair is not enough. For example: brushing a time range in view A filters view B, and selecting a category in view C highlights the matching records in views A and B. The two relationships must be genuinely different — the same brush feeding two charts at once counts as one relationship, not two.
Use a real coordination technique for each pair: brushing and linking, in which dragging a region in one view highlights or isolates the corresponding records elsewhere; or dynamic filters and queries, linking by tuple or by query, in which a selection filters the data feeding another view. An equivalent multiple-view coordination scheme of your own design is acceptable if you describe it in the write-up.
Coordination must be complete. A view that quietly ignores the current selection loses most of the credit for this element. Decide, and justify, whether a filtered view rescales its axes or holds them fixed for comparison.
The selection state must be visible and reversible. A viewer should be able to see what is currently selected — a highlighted brush region, an active filter chip, a count of matching records — and clear it with an obvious action.
Keep it responsive. Coordinated updates should feel immediate: filter on the client for continuous interactions such as dragging a brush, and use the backend for coarser queries. If an update is slow enough to notice, show that something is happening rather than freezing.
Document both pairs explicitly in your write-up, naming the source view, the dependent view, and what exactly happens to the dependent view when the interaction fires.
Bidirectional coordination, where any view can drive any other rather than only one designated master view, is not required — but it is the mark of a strong submission.
Hints:

Hold the selection in one shared state object and re-render dependent views from it. Do not let views push updates directly into each other; that is how you get an update loop you cannot debug.
d3.brush and d3.brushX give you the interaction; the work is in the handler, where you translate pixel extents back into data values with scale.invert.
Decide early between filtering (non-matching records disappear) and highlighting (they stay but recede). Highlighting preserves context, filtering gives detail — say which you chose and why.
Debounce server-backed updates by 100-200ms so dragging a brush does not fire fifty requests.
Animate between filtered states rather than snapping. A 300ms transition lets a viewer see what changed instead of guessing.
Test the empty selection and the select-everything case. Both are where coordinated dashboards usually break.
Required Element 3: A Full-Stack Website (4 points)
The deliverable is a running web application with a frontend and a backend, not a notebook and not a single static HTML file. Deploying it publicly is ideal; a project that runs on localhost is fully acceptable.

Backend. A server — FastAPI, Flask, Express or another framework of your choice — that loads the dataset at startup and exposes JSON endpoints over HTTP. At minimum it serves the data the dashboard needs; ideally it also answers filtered or aggregated queries, so the browser is not doing all the work.
Frontend. A web client that fetches from your API and renders the coordinated views. Plain HTML with D3, or React as in Lab Tutorial 1 — either is fine. No hard-coded data arrays pasted into the JavaScript: the data must come from the backend.
Runnable and documented. A README giving the exact commands to install and start both halves, the ports, and any environment variables. The grader will follow it literally on a clean machine.
Public webpage. Deploy your visualization so that anyone can open it — GitHub Pages is the easiest route for the frontend, and the walkthrough under Setting Up Your Environment covers it step by step. Put the live URL in your submission and confirm it loads in a private browser window.
If you cannot get the deployment working, a project that runs only on localhost is accepted with no penalty on this element. In that case the demo video is the only place the grader sees your tool running, so every required interaction must appear in it.
Robust performance and no noticeable bugs is the standard being graded here. Test the states you are least proud of: an empty selection, the largest filter, a fast repeated interaction.
Hints:

Get one end-to-end slice working first — one endpoint, one view, one fetch — before building the rest. A complete backend with no frontend is a week you cannot demo.
Keep the API base URL in one constant so localhost and a deployed host differ by one line.
Commit early and often, and push to GitHub. This project is large enough that losing it would genuinely hurt.
Try the deployment days before the deadline, not on the last night — GitHub Pages can take a while to go live, and backend hosts have their own surprises.
Required Element 4: Write-Up in a PDF Report (3 points)
Submit a brief, clear write-up as a PDF report (LastName_FirstName_A2_report.pdf), with screenshots of your dashboard where they support the argument. The dashboard shows what you built; the report shows why it is built that way.

A brief introduction to your dataset, its background, and the variables or the subset you chose.
The rationale for your design decisions: list the interactions you implemented, and explain how you chose your visual encodings and interaction techniques, what alternatives you considered, and how you arrived at your final choices.
Your exploration logic across views, including both coordination pairs from Required Element 2, and your system architecture — how the frontend and backend split the work, and why.
References to your data resources. List the data source you used, and cite any existing visualization examples your work adapts or builds on.
An overview of your development process: roughly how many hours you spent building the application, which aspects took the most time, and what went wrong along the way.
If any: a brief summary of AI usage — which tool, for what, and what you changed about the output.
If you are claiming extra credit: a clearly labelled "Extra Credit Features" section.
Argue rather than describe. "I used a bar chart" is a description; "I chose bars over a pie because the top categories are close in size and angular comparison hides that" is a rationale, and it is what earns the credit.
Hints:

Write the findings from your own dashboard, not from a pandas cell. If you cannot find your finding using your own tool, that is a design problem worth mentioning.
One honest limitation is worth more than a page of enthusiasm.
Include the sketch you made in Step 2 — a before-and-after of the design is one of the most convincing things a write-up can show.
Required Element 5: Demo Video (3 points)
A short screen recording with your own narration, required whether or not your site is deployed. Part of its purpose is to timestamp your project demo, so that the version being graded is fixed at the deadline.

It does not need to be polished or professionally voiced, but it must be short — a few minutes, four to six is a good target — functional, and it must clearly showcase every feature you implemented.
Analysis background and purpose. Open by explaining the dataset, why this analysis is worth doing, and the question you set out to answer.
The analysis process. Drive your own dashboard live: make a selection, show every linked view responding, narrate what that tells you, then follow the thread to the next question. This is the part that must show the coordination genuinely working.
The story. Close with what you concluded, supported by the dashboard states you just demonstrated, plus one honest limitation.
Practical requirements: 1080p, audible narration in your own voice, MP4 or an unlisted shareable link, and your name and the assignment stated at the start.
Innovation Insights — An example of how to present an interactive visual analytics project.

Funding the Frontier — An example of how to present an interactive visual analytics project.

Hints:

Write a short outline before recording. Six unrehearsed minutes usually contain three good ones.
Do not narrate the mouse. Narrate the inference: what the change in the linked views means for your question.
If your project runs only locally, this video is the entire live demonstration. Check the export and make sure nothing important is cut off or illegible.
Resources
zipdecode: Ben Fry's classic application of dynamic queries: typing digits of a zip code progressively narrows a map of the United States.
NameVoyager (archived): The same dynamic-query idea applied to a century of baby names — a good model for how one control can carry an entire exploration.
Treemaps (HCIL, University of Maryland): The technique originally developed to display hierarchical file structures, later adapted to entirely different data.
Map of the Market: The treemap re-purposed as an interactive map of the stock market — an example of matching a technique to a new problem.
Lab Tutorial 1: Build & Publish a Frontend Website: The React and GitHub Pages workflow you can reuse for the frontend half of this project.
Lab Tutorial 3: D3.js Interactions: Hover, brushing, tooltips, zoom and pan — the direct basis for Required Elements 1 and 2.
Lab Tutorial 4: D3.js Animation: Transitions between filtered states, so coordinated updates read as change rather than replacement.
D3.js documentation: Reference for selections, scales, axes, d3-brush and d3-zoom.
d3-brush: The brushing API behind linked selection, including how to read the selected extent in the event handler.
Observable D3 gallery: Worked examples of nearly every chart type and interaction technique in this assignment.
FastAPI documentation: The quickest Python path to a JSON API, with automatic interactive docs at /docs for testing your endpoints.
Flask quickstart: Alternative minimal Python backend, if you prefer Flask to FastAPI.
Express: getting started: Node backend option, if you would rather keep the whole project in JavaScript.
MDN: Using the Fetch API: How the frontend talks to your backend, including error handling and CORS behaviour.
GitHub Pages: The easiest way to publish your frontend, following the walkthrough in Step 5.
Tips for Success
Start small: Focus on a specific story or subset of your data. A polished, simple visualization is better than a sprawling, incomplete one.
Iterate: Test your design early and often, and share drafts with classmates for feedback before you commit to a layout.
Leverage resources: Use the class examples, the lab tutorials, the online D3 gallery, and the library documentation rather than deriving everything yourself.
Plan your time: Since you are working alone, set your own internal deadlines: dataset and sketch in the first week, one end-to-end view in the second, coordination and polish in the third, deployment and video with days to spare.
Deploy early: Get something — anything — live at least a couple of days before the deadline. Hosting problems are much easier to solve when they are not the last thing standing between you and the submission.
Overview
Getting Started
Setting Up Your Environment
Deliverables
Submitting
Formatting
Writeup
Scoring
Checklist
Assignment Requirements
Required Element 1: A List of Interactive Visualizations (7 points)
Required Element 2: Visualization Coordination (8 points)
Required Element 3: A Full-Stack Website (4 points)
Required Element 4: Write-Up in a PDF Report (3 points)
Required Element 5: Demo Video (3 points)
Resources
Tips for Success
Introduction to Data Visualization
Copyright © 2026 Yifang Wang
To dream the impossible dream.