create TABLE postsYT (
    id varchar(300) primary key,
    title varchar(120),
    textOfPost text,
    likes int,
    comment_count int,
    views int,
    videoLength varchar(120),
    postLink varchar(250),
    refLink text
);

create table comments (
    id varchar(300) primary key,
    comments text
);