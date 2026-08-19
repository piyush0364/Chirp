import {
	AdminServiceClient,
	AuthServiceClient,
	BookmarksServiceClient,
	CommentsServiceClient,
	FeedServiceClient,
	FollowsServiceClient,
	LikesServiceClient,
	NotificationsServiceClient,
	PostsServiceClient,
	SearchServiceClient,
	UsersServiceClient,
} from "@chirp/proto";
import { ChannelCredentials } from "@grpc/grpc-js";
import { GrpcTransport } from "@protobuf-ts/grpc-transport";

export interface ChirpClientConfig {
	host: string;
	secure?: boolean;
	apiKey?: string;
}

export interface ChirpClient {
	auth: AuthServiceClient;
	posts: PostsServiceClient;
	comments: CommentsServiceClient;
	likes: LikesServiceClient;
	follows: FollowsServiceClient;
	feed: FeedServiceClient;
	search: SearchServiceClient;
	users: UsersServiceClient;
	admin: AdminServiceClient;
	notifications: NotificationsServiceClient;
	bookmarks: BookmarksServiceClient;
	transport: GrpcTransport;
}

/**
 * Creates a gRPC client for the Chirp API
 */
export function createChirpClient(config: ChirpClientConfig): ChirpClient {
	const { host, secure = false, apiKey = "chirp-internal-api-key-dev" } = config;

	const channelCredentials = secure
		? ChannelCredentials.createSsl()
		: ChannelCredentials.createInsecure();

	const transport = new GrpcTransport({
		host,
		channelCredentials,
		interceptors: [
			{
				interceptUnary(next, method, input, options) {
					if (!options.meta) {
						options.meta = {};
					}
					options.meta["x-api-key"] = apiKey;
					return next(method, input, options);
				},
			},
		],
	});

	return {
		auth: new AuthServiceClient(transport),
		posts: new PostsServiceClient(transport),
		comments: new CommentsServiceClient(transport),
		likes: new LikesServiceClient(transport),
		follows: new FollowsServiceClient(transport),
		feed: new FeedServiceClient(transport),
		search: new SearchServiceClient(transport),
		users: new UsersServiceClient(transport),
		admin: new AdminServiceClient(transport),
		notifications: new NotificationsServiceClient(transport),
		bookmarks: new BookmarksServiceClient(transport),
		transport,
	};
}

/**
 * Default API host for development
 */
export const DEFAULT_GRPC_HOST = "localhost:50051";
