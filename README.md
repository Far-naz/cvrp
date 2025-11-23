# multi-period cvrp
Your stakeholder is a materials vendor to a company that has multiple factories around the country. The
vendor wants to schedule the optimal delivery routes to ensure that the orders get delivered with the
lowest possible cost.
The main constraints that need to be satisfied are:
    - Trucks cannot be overloaded, neither in weight nor in volume.
    - An item is only available for pick up by a specific time. A truck can start only when all items
    assigned to it are available.
    - All items must be delivered at their destinations before their deadlines.
    - A truck can make at most 5 stops.
    - A truck must stay at each stop for 1 hours to unload the items. Each stop will incur a cost of 1 in
    addition to the delivery cost.
Implement an algorithm that will propose the lowest cost routes for the deliveries, given the constraints
above. You are free to choose the tools you consider best suited to the task.


Based on Kaggle dataset: https://www.kaggle.com/datasets/mexwell/large-scale-route-optimization?select=order_small.csv

