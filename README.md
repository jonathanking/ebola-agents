# csm_project
Cell &amp; Systems Modeling Final Project

### An  Agent­Based  Approach  to  Modeling  Ebola  Outbreak

### Introduction

The    2014 ­ 2016    Western Africa Ebola epidemic marked the largest outbreak of the disease ever
recorded. During this time, some    28 , 616    confirmed or suspected cases were reported across Sierra Leone,
Guinea, and Liberia. Even with the intervention of concerted humanitarian aid and directed relief efforts,
11 , 310    people in total died as a result.  1        As a result the World Health Organization (WHO) named Ebola an
emerging disease likely to induce a major epidemic in December    2015.  2

In order to learn what fundamental attributes drive the spread of disease, it is beneficial to create
models that simulate real­life events. A common model of disease spread is the SEIR model. SEIR
models work by categorizing members of some population as either _S_ usceptible, _E_ xposed, _I_ nfected, or
_R_ emoved. By defining rates by which members transition between each of these categories and altering
the parameters that affect these rates, we can observe how a population exposed to disease changes over
time. One such parameter is the reproduction number, _R_ 0 , t he average n umber of s econdary cases
spawned by a primary case. In Ebola, this measure has been estimated to be two, meaning an infected
individual will pass the disease to two others.  3        SEIR models are often described by ordinary differential
equations (ODEs), and related work of this nature is discussed further below.

One drawback of standard ODE­based SEIR models is that they do not directly account for the
stochastic nature by which infected members of a population can interact with each other. As infected
individuals travel, they risk spreading disease among the rest of the population. While the disease
progression for Ebola is relatively quick and dramatic, the initial symptoms are fairly benign, such as fever
and fatigue. Thus it is conceivable that there exists a window whereby symptomatic individuals could still
interact with others before becoming immobile. Another drawback with ODE­based SEIR models is that
they do not account for spatial constraints that could impact disease spread. Chowell et. al. ( 2015 )
performed statistical analyses on data generated during the West African Ebola outbreak and found that
disease spreads at a polynomial rate on a local level, but exponentially at a broader global scale.  4        This
suggests that there could be some underlying phenomena related to the way populations are distributed in
space that could affect disease transmission, and merits further investigation.

This work presents the design and implementation of a novel agent­based model of Ebola
disease spread that aims to improve upon traditional SEIR models by incorporating stochasticity and spatial
constraints that are motivated by real­life conditions. In our model, virtual Agents inhabit nodes of a
connected grid and may move randomly to a neighboring node at each time step. By ascribing each Agent
one of the SEIR conditions and allowing them to change state based on their interactions with other agents
at a common node, we can connect emergent properties that arise in our model to real­world interactions.
On the whole, we would like to determine how effectively our model can emulate the spread of Ebola.

In constructing a new model, there are a number of considerations we must make to evaluate its
validity. First, we want to make sure that it correctly captures known behaviors. As an example, if we
increase t he disease m odel’s reproduction number, _R_ 0 , the m odel s hould p redict that p eople n ot only
become infected at a quicker rate but are also removed much faster. Furthermore, we want to test the
model’s robustness by observing its behavior as we vary input parameters, such as the probabilities that
Agents move away from a node, or the times for which an Agent inhabits a given SEIR condition. This is
important since a model that is too sensitive may have too small a parameter search space to yield
biologically significant results and, conversely, a model that lacks sensitivity may never demonstrate
meaningful behaviors.

Finally, we want to utilize our choice of model parameters to elucidate behaviors associated with
constraining the movement of Agents as well as constraining the grid’s structure. These two constraints are
the best means by which we attempt to transform our abstract model into a clearer picture of reality.
Constraining infected Agent movement is analogous to the relative immobility of sick individuals, and
constraints on the graph’s connectivity impose barriers to movement and add a layer of nonuniformity
more representative of the real world. By comparing our model with and without these constraints, we can
determine whether or not Agent­based models can uncover large­scale behavior of disease spread.
