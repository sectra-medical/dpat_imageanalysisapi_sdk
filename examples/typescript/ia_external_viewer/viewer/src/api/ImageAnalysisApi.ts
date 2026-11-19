import type { Application } from "../models/Application"
import type { CaseImage, Image } from "../models/ImageInfo"
import type { Exam } from "../models/Exam"

import type { Result } from "../models/Result"

export interface IImageAnalysisApiClient {
    /**
     * Launch against Pathology Image Analysis API.
     * @param launchUrl The launch url towards Pathology Image Analysis API.
     * @returns Launch response.
     */
    launchAsync(launchUrl: string): Promise<Exam>;

    /**
     * Get image metadata for specific request.
     * @param accessionNumber The accession number of the request.
     * @param accessionNumberIssuer Optional accession number issuer of the request.
     * @returns List of image metadata.
     */
    getImagesInRequestAsync(accessionNumber: string, accessionNumberIssuer?: string): Promise<CaseImage[]>;

    /**
     * Get image metadata for slide.
     * @param slideId The slide ID.
     * @returns Image metadata.
     */
    getImageAsync(slideId: string): Promise<Image>;

    /**
     * Get tile from Pathology Image Analysis API.
     * @param slideId The slide to get tile for.
     * @param level The level to get tile for.
     * @param x The x coordinate of the tile.
     * @param y The y coordinate of the tile.
     * @param z The z coordinate of the tile.
     * @param extension The extension of the tile format to get.
     * @param channels The channels to get.
     * @returns The tile in bytes.
     */
    getTileAsync(
        slideId: string,
        level: number,
        x: number,
        y: number,
        z: string,
        extension: string,
        channels?: string
    ): Promise<Uint8Array>;

    /**
     * Get slide label image for slide.
     * @param slideId The slide to get label for.
     * @returns Slide label image data.
     */
    getSlideLabelAsync(slideId: string): Promise<Uint8Array>;

    /**
     * Get metadata on registered application.
     * @returns Application metadata.
     */
    getApplicationAsync(): Promise<Application>;

    /**
     * Store result.
     * @param result Result to store.
     * @returns Stored result.
     */
    storeResultAsync(result: Result): Promise<Result>;

    /**
     * Get result.
     * @param resultId The id of the result.
     * @returns Retrieved result.
     */
    getResultAsync(resultId: string): Promise<Result>;

    /**
     * Modify stored result.
     * @param result Result to modify.
     * @returns Modified result.
     */
    modifyResultAsync(result: Result): Promise<Result>;

    /**
     * Return list of results for slide.
     * @param slideId Slide id.
     * @returns List of results for slide id.
     */
    getResultsForSlideAsync(slideId: string): Promise<Result[]>;

    /**
     * Download attachment for result.
     * @param resultId The id of the result.
     * @param attachmentName Attachment name.
     * @param start Optional start position of attachment to read.
     * @param end Optional end position of attachment to read.
     * @returns Attachment data in bytes.
     */
    downloadAttachmentAsync(
        resultId: string,
        attachmentName: string,
        start?: number,
        end?: number
    ): Promise<Uint8Array>;
}

export interface IImageAnalysisApiClientConfiguration {
    apiVersion: string;
    applicationVersion: string;
    applicationId: string;
}

export class ImageAnalysisApiClientUnauthorizedException extends Error {
    constructor(message?: string) {
        super(message);
        this.name = 'ImageAnalysisApiClientUnauthorizedException';
    }
}

export class ImageAnalysisApiClient implements IImageAnalysisApiClient {
    private readonly configuration: IImageAnalysisApiClientConfiguration;
    private readonly versionHeader: Record<string, string>;
    private readonly controller = "/api/image_analysis";

    constructor(configuration: IImageAnalysisApiClientConfiguration) {
        this.configuration = configuration;
        this.versionHeader = {
            "X-Sectra-ApiVersion": configuration.apiVersion,
            "X-Sectra-SoftwareVersion": configuration.applicationVersion
        };
    }

    async launchAsync(launch_url: string): Promise<Exam> {
        const url = `${this.controller}/launch`;
        const launchRequest = {
            launchUrl: launch_url,
            appId: this.configuration.applicationId
        };
        return await this.postAsync<Exam>(url, launchRequest);
    }

    async getImagesInRequestAsync(accessionNumber: string, accessionNumberIssuer?: string): Promise<CaseImage[]> {
        let url = `${this.controller}/requests/${accessionNumber}/images/info`;
        if (accessionNumberIssuer) {
            url += `?accessionNumberIssuer=${encodeURIComponent(accessionNumberIssuer)}`;
        }
        return await this.getAsync<CaseImage[]>(url);
    }

    async getImageAsync(slideId: string): Promise<Image> {
        const url = `${this.controller}/slides/${slideId}/info`;
        return await this.getAsync<Image>(url);
    }

    async getTileAsync(
        slideId: string,
        level: number,
        x: number,
        y: number,
        z: string,
        extension: string,
        channels?: string
    ): Promise<Uint8Array> {
        const url = `${this.controller}/images/${slideId}_files/${level}/${x}_${y}_${z}.${extension}` +
            (channels ? `?channels=${channels}` : "");
        return await this.getBytes(url);
    }

    async getSlideLabelAsync(slideId: string): Promise<Uint8Array> {
        const url = `${this.controller}/slides/${slideId}/label`;
        return await this.getBytes(url);
    }

    async getApplicationAsync(): Promise<Application> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}`;
        return await this.getAsync<Application>(url);
    }

    async storeResultAsync(result: Result): Promise<Result> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}/results/`;
        return await this.postAsync<Result>(url, result);
    }

    async getResultAsync(resultId: string): Promise<Result> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}/results/${resultId}`;
        return await this.getAsync<Result>(url);
    }

    async modifyResultAsync(result: Result): Promise<Result> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}/results/${result.id}`;
        return await this.putAsync<Result>(url, result);
    }

    async getResultsForSlideAsync(slideId: string): Promise<Result[]> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}/results/slide/${slideId}`;
        return await this.getAsync<Result[]>(url);
    }

    async downloadAttachmentAsync(
        resultId: string,
        attachmentName: string,
        start?: number,
        end?: number
    ): Promise<Uint8Array> {
        const url = `${this.controller}/applications/${this.configuration.applicationId}/results/${resultId}/attachments?name=${encodeURIComponent(attachmentName)}`;
        return await this.getBytes(url, start, end);
    }

    private async getBytes(url: string, start?: number, end?: number): Promise<Uint8Array> {
        const headers = { ...this.versionHeader };
        if (start !== undefined && end !== undefined) {
            headers['Range'] = `bytes=${start}-${end}`;
        }
        const response = await fetch(url, { method: 'GET', headers: headers});
        if (!response.ok) {
            if (response.status === 401) {
                throw new ImageAnalysisApiClientUnauthorizedException();
            }
            throw new Error(
                `Failed to get bytes from ${url}. Got response status ${response.status} ` +
                `and reason ${response.statusText}.`
            );
        }
        return new Uint8Array(await response.arrayBuffer());
    }

    private async getAsync<T>(url: string): Promise<T> {
        const headers = this.versionHeader
        const response = await fetch(url, { method: 'GET', headers: headers});
        if (!response.ok) {
            if (response.status === 401) {
                throw new ImageAnalysisApiClientUnauthorizedException();
            }
            throw new Error(
                `Failed to get from ${url}. Got response status ${response.status} ` +
                `and reason ${response.statusText}.`
            );
        }
        return await this.parseFromResponse<T>(response);
    }

    private async putAsync<T>(url: string, item: T): Promise<T> {
        const headers = {...this.versionHeader, "Content-Type": "application/json" };
        const response = await fetch(url, { method: 'PUT', headers: headers, body: JSON.stringify(item) });
        if (!response.ok) {
            if (response.status === 401) {
                throw new ImageAnalysisApiClientUnauthorizedException();
            }
            throw new Error(
                `Failed to put to ${url}. Got response status ${response.status} ` +
                `and reason ${response.statusText}.`
            );
        }
        return await this.parseFromResponse<T>(response);
    }

    private async postAsync<T>(url: string, item: object): Promise<T> {
        const headers = {...this.versionHeader, "Content-Type": "application/json" };
        const response = await fetch(url, { method: 'POST', headers: headers, body: JSON.stringify(item) });
        if (!response.ok) {
            if (response.status === 401) {
                throw new ImageAnalysisApiClientUnauthorizedException();
            }
            throw new Error(
                `Failed to post to ${url}. Got response status ${response.status} ` +
                `and reason ${response.statusText}.`
            );
        }
        return await this.parseFromResponse<T>(response);
    }

    private async parseFromResponse<T>(response: Response): Promise<T> {
        try {
            const content = await response.text();
            const result = JSON.parse(content) as T;
            if (result == null) {
                throw new Error(`Failed to deserialize ${content}`);
            }
            return result;
        } catch (exception) {
            throw new Error(`Failed to deserialize: ${exception}`);
        }
    }
}
